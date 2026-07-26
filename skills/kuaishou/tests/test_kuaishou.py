"""Guards for the kuaishou skill script — no network, stdlib only."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "kuaishou.py"


def _load(argv):
    """Import the script fresh with a given argv so module-level CONFIRM re-evaluates."""
    old = sys.argv
    sys.argv = ["kuaishou.py", *argv]
    try:
        spec = importlib.util.spec_from_file_location(f"ks_{len(argv)}_{abs(hash(tuple(argv)))}", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.argv = old


def _run(args, env=None):
    e = {**os.environ, "KUAISHOU_TOKEN": "tok", "KUAISHOU_APP_ID": "aid", **(env or {})}
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, env=e)


class TestConfirmGate(unittest.TestCase):
    def test_confirm_only_honored_as_last_argument(self):
        self.assertTrue(_load(["publish", "--caption", "t", "--confirm"]).CONFIRM)
        # A caption that merely contains the flag must NOT self-authorize.
        mod = _load(["publish", "--caption", "--confirm", "--video-url", "u"])
        self.assertFalse(mod.CONFIRM)

    def test_publish_without_confirm_is_a_dry_run(self):
        r = _run(
            [
                "publish",
                "--caption",
                "标题",
                "--video-url",
                "https://cdn.acedata.cloud/a.mp4",
                "--cover-url",
                "https://cdn.acedata.cloud/a.jpg",
            ]
        )
        self.assertEqual(r.returncode, 0)
        self.assertTrue(json.loads(r.stdout)["dry_run"])


class TestRequiredInputs(unittest.TestCase):
    def test_missing_token_fails_clearly(self):
        r = _run(["whoami"], env={"KUAISHOU_TOKEN": ""})
        self.assertEqual(r.returncode, 1)
        self.assertIn("KUAISHOU_TOKEN", json.loads(r.stdout)["error"])

    def test_missing_app_id_fails_clearly(self):
        r = _run(["whoami"], env={"KUAISHOU_APP_ID": ""})
        self.assertEqual(r.returncode, 1)
        self.assertIn("KUAISHOU_APP_ID", json.loads(r.stdout)["error"])

    def test_cover_is_required(self):
        r = _run(["publish", "--caption", "t", "--video-url", "https://cdn.acedata.cloud/a.mp4"])
        self.assertEqual(r.returncode, 1)
        self.assertIn("cover", json.loads(r.stdout)["error"])


class TestUpstreamSemantics(unittest.TestCase):
    def test_result_not_one_is_a_failure_despite_http_200(self):
        mod = _load(["whoami"])
        with self.assertRaises(RuntimeError):
            mod._check({"result": 100200108, "error_msg": "expired"}, "user_info")
        self.assertEqual(mod._check({"result": 1, "x": 2}, "ok")["x"], 2)

    def test_private_media_hosts_are_blocked(self):
        mod = _load(["whoami"])
        for url in (
            "http://127.0.0.1/a.mp4",
            "http://localhost/a.mp4",
            "file:///etc/passwd",
            "http://2130706433/a.mp4",  # decimal
            "http://0x7f000001/a.mp4",  # hex
            "http://[::1]/a.mp4",  # IPv6 loopback
            "http://169.254.169.254/latest/meta-data/",  # cloud metadata
            # Allowlisted-looking but not actually ours (DNS rebinding vector).
            "https://evil.example/a.mp4",
            "https://cdn.acedata.cloud.evil.example/a.mp4",
        ):
            with self.assertRaises(RuntimeError, msg=url):
                mod._assert_public_url(url)

    def test_own_cdn_is_allowed(self):
        mod = _load(["whoami"])
        # Mocked so the suite stays offline-safe.
        with unittest.mock.patch.object(
            mod.socket, "getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 0))]
        ):
            mod._assert_public_url("https://cdn.acedata.cloud/x.mp4")  # must not raise

    def test_credentials_are_redacted_from_errors(self):
        mod = _load(["whoami"])
        leaked = '{"error_msg":"bad","access_token":"secret-abc","upload_token":"up-xyz"}'
        red = mod._redact(leaked)
        self.assertNotIn("secret-abc", red)
        self.assertNotIn("up-xyz", red)
        with self.assertRaises(RuntimeError) as cm:
            mod._check({"result": 2, "access_token": "secret-abc"}, "publish")
        self.assertNotIn("secret-abc", str(cm.exception))


class _FakeResp:
    def __init__(self, payload):
        self._b = json.dumps(payload).encode()

    def read(self, *a):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestHttpContract(unittest.TestCase):
    """Assert the actual requests, so a wrong param/verb can't pass silently."""

    def _capture(self, mod, payload=None):
        calls = []

        def fake(req, timeout=None):
            calls.append(req)
            return _FakeResp(payload if payload is not None else {"result": 1})

        return calls, fake

    def test_direct_upload_posts_raw_bytes_with_token_in_query(self):
        mod = _load(["whoami"])
        calls, fake = self._capture(mod)
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as fh:
            fh.write(b"v" * 1024)
            path = fh.name
        try:
            with unittest.mock.patch.object(mod.urllib.request, "urlopen", fake):
                mod._upload_binary("up.example.com", "utok", path, 1024)
        finally:
            os.unlink(path)
        self.assertEqual(len(calls), 1)
        req = calls[0]
        self.assertEqual(req.get_method(), "POST")
        self.assertTrue(req.full_url.startswith("http://up.example.com/api/upload?"))
        self.assertIn("upload_token=utok", req.full_url)
        self.assertEqual(req.data, b"v" * 1024)  # raw body, not multipart

    def test_fragmented_upload_ids_start_at_zero_then_completes(self):
        mod = _load(["whoami"])
        calls, fake = self._capture(mod)
        size = mod.CHUNK * 2 + 7
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as fh:
            fh.write(b"v" * size)
            path = fh.name
        try:
            with unittest.mock.patch.object(mod.urllib.request, "urlopen", fake):
                mod._upload_binary("up.example.com", "utok", path, size)
        finally:
            os.unlink(path)
        urls = [c.full_url for c in calls]
        self.assertEqual(len(urls), 4)  # 3 fragments + complete
        self.assertIn("fragment_id=0", urls[0])
        self.assertIn("fragment_id=2", urls[2])
        self.assertIn("fragment_count=3", urls[3])
        self.assertTrue(urls[3].startswith("http://up.example.com/api/upload/complete?"))
        # EVERY fragment carries at most one chunk, never the whole remainder.
        frags = [c for c in calls if "/api/upload/fragment?" in c.full_url]
        self.assertEqual(len(frags), 3)
        for i, f in enumerate(frags):
            self.assertLessEqual(len(f.data), mod.CHUNK, f"fragment {i} too big")
        self.assertEqual(sum(len(f.data) for f in frags), size)

    def test_publish_sends_upload_token_in_query_and_cover_in_multipart(self):
        mod = _load(["whoami"])
        calls = []

        def fake(req, timeout=None):
            calls.append(req)
            if "start_upload" in req.full_url:
                return _FakeResp({"result": 1, "upload_token": "utok", "endpoint": "up.example.com"})
            if "photo/publish" in req.full_url:
                return _FakeResp({"result": 1, "video_info": {"photo_id": "pid", "caption": "标题"}})
            return _FakeResp({"result": 1})

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as v:
            v.write(b"v" * 512)
            vpath = v.name
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as c:
            c.write(b"c" * 32)
            cpath = c.name
        try:
            with unittest.mock.patch.object(mod.urllib.request, "urlopen", fake), unittest.mock.patch.dict(
                os.environ, {"KUAISHOU_TOKEN": "tok", "KUAISHOU_APP_ID": "aid"}
            ):
                args = mod.argparse.Namespace(
                    caption="标题",
                    video_url=None,
                    video_file=vpath,
                    cover_url=None,
                    cover_file=cpath,
                    stereo_type=None,
                    product_id=None,
                )
                mod.CONFIRM = True
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    mod.cmd_publish(args)
                result = json.loads(buf.getvalue())
        finally:
            os.unlink(vpath)
            os.unlink(cpath)

        self.assertTrue(result["published"])
        self.assertEqual(result["photo_id"], "pid")
        pub = [c for c in calls if "photo/publish" in c.full_url][0]
        self.assertEqual(pub.get_method(), "POST")
        # upload_token rides the query string; cover/caption ride the body.
        self.assertIn("upload_token=utok", pub.full_url)
        self.assertIn("access_token=tok", pub.full_url)
        self.assertTrue(pub.headers["Content-type"].startswith("multipart/form-data; boundary="))
        self.assertIn(b'name="cover"; filename="cover.jpg"', pub.data)
        self.assertIn("标题".encode(), pub.data)
        start = [c for c in calls if "start_upload" in c.full_url][0]
        self.assertEqual(start.get_method(), "POST")


if __name__ == "__main__":
    unittest.main()
