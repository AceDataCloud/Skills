from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import unittest
import urllib.error
from email.message import Message
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


def load_script(name, relative):
    script = Path(__file__).parents[1] / "skills" / relative
    spec = importlib.util.spec_from_file_location(name, script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


medium = load_script("medium_runtime_errors", "medium/scripts/medium.py")
zhihu = load_script("zhihu_runtime_errors", "zhihu/scripts/blog.py")
URL = "https://synthetic.example.invalid/profile"
JAR = [{"name": "session", "value": "synthetic-private-cookie"}]
# Independent expectation: never derive the accepted wire contract from the module.
KNOWN_REASONS = (
    "cookie_scope_denied", "cookie_response_denied", "cookie_mirror_denied",
    "cookie_domain_denied", "credential_slot_denied", "request_denied",
    "request_refused", "response_refused", "redirect_denied", "lease_expired",
    "lease_denied", "policy_changed", "upstream_unavailable",
)


class ConnectorRuntimeErrorsTests(unittest.TestCase):
    def invoke(self, surface, method="GET"):
        if surface == "medium_api":
            return medium.api(method, URL, JAR)
        if surface == "medium_gql":
            return medium.gql(JAR, "UserProfileQuery", {})
        return zhihu.get_json(URL, JAR)

    def failure(self, surface, status, body, method="GET"):
        module = medium if surface.startswith("medium") else zhihu
        output = io.StringIO()
        with patch.object(module, "request", return_value=(status, body)) as request, \
                patch.object(medium.time, "sleep") as sleep, \
                contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as exc:
            self.invoke(surface, method)
        self.assertEqual(exc.exception.code, 1)
        self.assertNotIn("synthetic-private-cookie", output.getvalue())
        return json.loads(output.getvalue()), request.call_count, sleep.call_count

    def assert_no_expiry_guess(self, result):
        self.assertNotIn("cookie likely expired", result["error"])
        self.assertNotIn("cookie is likely expired", result["error"])
        self.assertNotIn("Reconnect", result["error"])

    def test_exact_proxy_envelopes_keep_codes_without_retrying(self):
        for surface in ("medium_api", "medium_gql", "zhihu"):
            for reason in KNOWN_REASONS:
                with self.subTest(surface=surface, reason=reason):
                    result, calls, sleeps = self.failure(surface, 403, json.dumps({"error": reason}))
                    self.assertEqual(result["error_code"], reason)
                    self.assertIn("connector runtime error (403)", result["error"])
                    self.assert_no_expiry_guess(result)
                    self.assertEqual((calls, sleeps), (1, 0))

    def test_auth_status_alone_does_not_establish_expired_credentials(self):
        for surface in ("medium_api", "medium_gql", "zhihu"):
            for status in (401, 403):
                with self.subTest(surface=surface, status=status):
                    result, _, _ = self.failure(surface, status, '{"message":"login required"}')
                    self.assertIn(f"HTTP {status}", result["error"])
                    self.assertNotIn("error_code", result)
                    self.assert_no_expiry_guess(result)

    def test_non_proxy_envelopes_are_not_reclassified(self):
        bodies = [
            json.dumps({"error": "unknown_reason"}),
            json.dumps({"error": "response_refused", "code": 403}),
            json.dumps({"error": {"message": "response_refused"}}),
            json.dumps({"error": ["response_refused"]}),
            json.dumps(["response_refused"]),
            json.dumps([["error", "response_refused"]]),
            '{"error":"other","error":"response_refused"}',
            " " * 257 + '{"error":"response_refused"}',
            ")] } malformed JSON",
            "<html>403 access denied</html>",
        ]
        for surface in ("medium_api", "medium_gql", "zhihu"):
            for body in bodies:
                with self.subTest(surface=surface, body=body):
                    result, _, _ = self.failure(surface, 403, body)
                    self.assertNotIn("error_code", result)
                    self.assertIn("HTTP 403", result["error"])
                    self.assert_no_expiry_guess(result)

    def test_proxy_literal_on_401_is_not_reclassified(self):
        for surface in ("medium_api", "medium_gql", "zhihu"):
            with self.subTest(surface=surface):
                result, _, _ = self.failure(surface, 401, '{"error":"response_refused"}')
                self.assertNotIn("error_code", result)
                self.assertIn("HTTP 401", result["error"])

    def test_medium_prefixed_response_is_not_a_proxy_envelope(self):
        result, calls, sleeps = self.failure(
            "medium_api", 403, '])}while(1);</x>{"error":"response_refused"}'
        )
        self.assertNotIn("error_code", result)
        self.assertEqual((calls, sleeps), (2, 1))

    def test_successful_payloads_remain_unchanged(self):
        payload = {"error": "response_refused", "profile": {"id": "synthetic"}}
        with patch.object(medium, "request", return_value=(200, json.dumps(payload))):
            self.assertEqual(self.invoke("medium_api"), payload)
        with patch.object(zhihu, "request", return_value=(200, json.dumps(payload))):
            self.assertEqual(self.invoke("zhihu"), (200, payload))
        with patch.object(medium, "request", return_value=(200, json.dumps({"data": payload}))):
            self.assertEqual(self.invoke("medium_gql"), payload)
        with patch.object(medium, "request", return_value=(200, "])}while(1);</x>" + json.dumps(payload))):
            self.assertEqual(self.invoke("medium_api"), payload)
        # Match the exact proxy body, changing only the HTTP status.
        exact = {"error": "response_refused"}
        with patch.object(medium, "request", return_value=(200, json.dumps(exact))):
            self.assertEqual(self.invoke("medium_api"), exact)
            self.assertEqual(self.invoke("medium_gql"), {})
        with patch.object(zhihu, "request", return_value=(200, json.dumps(exact))):
            self.assertEqual(self.invoke("zhihu"), (200, exact))

    def test_medium_keeps_one_get_retry_for_other_403_and_429_responses(self):
        for status in (403, 429):
            with self.subTest(status=status), \
                    patch.object(medium, "request", side_effect=[(status, "<html>blocked</html>"), (200, '{"ok":true}')]) as request, \
                    patch.object(medium.time, "sleep") as sleep:
                self.assertEqual(self.invoke("medium_api"), {"ok": True})
                self.assertEqual(request.call_count, 2)
                sleep.assert_called_once()

    def test_medium_never_replays_posts_on_proxy_or_provider_failures(self):
        for body in ('{"error":"upstream_unavailable"}', '<html>403</html>'):
            with self.subTest(body=body):
                _, calls, sleeps = self.failure("medium_api", 403, body, method="POST")
                self.assertEqual((calls, sleeps), (1, 0))

    def test_medium_xsrf_bootstrap_preserves_proxy_refusal(self):
        error = urllib.error.HTTPError(
            URL, 403, "Forbidden", Message(), io.BytesIO(b'{"error":"cookie_response_denied"}')
        )
        output = io.StringIO()
        with patch.object(medium.urllib.request, "urlopen", side_effect=error) as request, \
                contextlib.redirect_stdout(output), self.assertRaises(SystemExit):
            medium.prime_xsrf([])
        request.assert_called_once()
        self.assertEqual(json.loads(output.getvalue())["error_code"], "cookie_response_denied")

    def test_medium_xsrf_bootstrap_keeps_non_proxy_cookie_handling(self):
        headers = Message()
        headers.add_header("Set-Cookie", "xsrf=synthetic-xsrf; Path=/")
        error = urllib.error.HTTPError(URL, 403, "Forbidden", headers, io.BytesIO(b"upstream response"))
        jar = []
        with patch.object(medium.urllib.request, "urlopen", side_effect=error):
            medium.prime_xsrf(jar)
        self.assertEqual(medium.cookie_value(jar, "xsrf"), "synthetic-xsrf")

    def test_missing_xsrf_stops_before_writing_without_expiry_guess(self):
        args = SimpleNamespace(title="Synthetic", content="body", content_file=None)
        output = io.StringIO()
        with patch.object(medium, "CONFIRM", True), patch.object(medium, "prime_xsrf"), \
                patch.object(medium, "api") as api, contextlib.redirect_stdout(output), \
                self.assertRaises(SystemExit):
            medium.cmd_publish([], args)
        api.assert_not_called()
        message = json.loads(output.getvalue())["error"]
        self.assertIn("xsrf", message)
        self.assertNotIn("expired", message)
        self.assertNotIn("reconnect", message.lower())


if __name__ == "__main__":
    unittest.main()
