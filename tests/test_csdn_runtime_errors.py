from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).parents[1] / "skills" / "csdn" / "scripts" / "csdn.py"
SPEC = importlib.util.spec_from_file_location("csdn_runtime_errors", SCRIPT)
assert SPEC and SPEC.loader
csdn = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(csdn)

URL = "https://synthetic.example.invalid/articles"
JAR = [{"name": "session", "value": "synthetic-private-cookie"}]


class CsdnRuntimeErrorTests(unittest.TestCase):
    def call(self, status, body):
        with patch.object(csdn, "request", return_value=(status, body)) as request:
            result = csdn.get_json(URL, JAR, referer=URL, origin=URL)
        request.assert_called_once_with("GET", URL, JAR, referer=URL, origin=URL)
        return result

    def failure(self, status, body):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as exc:
            self.call(status, body)
        self.assertEqual(exc.exception.code, 1)
        self.assertNotIn("synthetic-private-cookie", output.getvalue())
        return json.loads(output.getvalue())

    def test_known_proxy_reasons_keep_their_code_without_reconnect_advice(self):
        for reason in (
            "cookie_response_denied", "request_denied", "response_refused",
            "redirect_denied", "lease_expired", "upstream_unavailable",
        ):
            with self.subTest(reason=reason):
                result = self.failure(403, json.dumps({"error": reason}))
                self.assertEqual(result["error_code"], reason)
                self.assertIn(reason, result["error"])
                self.assertIn("connector runtime error (403)", result["error"])
                self.assertNotIn("cookie likely expired", result["error"])
                self.assertNotIn("Reconnect", result["error"])

    def test_upstream_auth_rejections_keep_existing_guidance(self):
        for status in (401, 403):
            with self.subTest(status=status):
                result = self.failure(status, json.dumps({"code": status, "message": "login required"}))
                self.assertNotIn("error_code", result)
                self.assertIn(f"auth failed ({status})", result["error"])
                self.assertIn("Reconnect", result["error"])

    def test_upstream_waf_rejection_keeps_existing_guidance(self):
        result = self.failure(403, "<html>WAF 403</html>")
        self.assertIn("CSDN WAF blocked", result["error"])
        self.assertNotIn("error_code", result)

    def test_non_proxy_error_envelopes_do_not_match(self):
        for payload in (
            {"error": "unknown_reason"},
            {"error": "request_denied", "code": 403},
            {"error": {"reason": "request_denied"}},
            {"error": ["request_denied"]},
            ["request_denied"],
        ):
            with self.subTest(payload=payload):
                result = self.failure(403, json.dumps(payload))
                self.assertNotIn("error_code", result)
                self.assertIn("auth failed (403)", result["error"])

    def test_proxy_reason_under_upstream_401_is_not_reclassified(self):
        result = self.failure(401, json.dumps({"error": "request_denied"}))
        self.assertNotIn("error_code", result)
        self.assertIn("auth failed (401)", result["error"])

    def test_successful_json_is_unchanged(self):
        for payload in ({"code": 200, "data": {"list": [], "total": 0}}, {"error": "request_denied"}, None):
            with self.subTest(payload=payload):
                self.assertEqual(self.call(200, json.dumps(payload)), payload)

    def test_non_json_error_retains_existing_behavior(self):
        result = self.failure(502, "temporary upstream failure")
        self.assertIn("non-JSON response (502)", result["error"])
        self.assertNotIn("error_code", result)


if __name__ == "__main__":
    unittest.main()
