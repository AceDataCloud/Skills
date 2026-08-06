import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).parents[1] / "skills" / "tiktok" / "scripts" / "tiktok.py"
spec = importlib.util.spec_from_file_location("tiktok_script", MODULE_PATH)
tiktok = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(tiktok)


class Response:
    def __init__(self, payload=None, status=200):
        self.payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload or {}).encode()


class TikTokScriptTests(unittest.TestCase):
    def setUp(self):
        self.token_patch = patch.dict(os.environ, {"TIKTOK_TOKEN": "secret-token"})
        self.token_patch.start()

    def tearDown(self):
        self.token_patch.stop()

    def test_file_upload_initializes_and_puts_one_chunk(self):
        init = Response({"data": {"publish_id": "pub_1", "upload_url": "https://upload.test/one"}, "error": {"code": "ok"}})
        uploaded = Response(status=201)
        stdout = io.StringIO()
        with tempfile.NamedTemporaryFile(suffix=".mp4") as video:
            video.write(b"video-bytes")
            video.flush()
            with patch("urllib.request.urlopen", side_effect=[init, uploaded]) as mocked, patch(
                "sys.argv", ["tiktok.py", "upload", video.name]
            ), redirect_stdout(stdout):
                tiktok.main()

        init_request, put_request = [call.args[0] for call in mocked.call_args_list]
        self.assertTrue(init_request.full_url.endswith("/post/publish/inbox/video/init/"))
        self.assertEqual(
            json.loads(init_request.data),
            {"source_info": {"source": "FILE_UPLOAD", "video_size": 11, "chunk_size": 11, "total_chunk_count": 1}},
        )
        self.assertEqual(put_request.method, "PUT")
        self.assertEqual(put_request.data, b"video-bytes")
        self.assertEqual(put_request.headers["Content-range"], "bytes 0-10/11")
        rendered = stdout.getvalue()
        self.assertNotIn("secret-token", rendered)
        self.assertEqual(json.loads(rendered)["data"]["publish_id"], "pub_1")

    def test_status_fetch_posts_publish_id(self):
        with patch(
            "urllib.request.urlopen",
            return_value=Response({"data": {"status": "SEND_TO_USER_INBOX"}, "error": {"code": "ok"}}),
        ) as mocked, patch("sys.argv", ["tiktok.py", "status", "pub_1"]), redirect_stdout(io.StringIO()):
            tiktok.main()
        self.assertEqual(json.loads(mocked.call_args.args[0].data), {"publish_id": "pub_1"})

    def test_api_error_is_structured(self):
        stdout = io.StringIO()
        with patch(
            "urllib.request.urlopen",
            return_value=Response({"data": {}, "error": {"code": "spam_risk", "message": "blocked"}}),
        ), self.assertRaises(SystemExit), redirect_stdout(stdout):
            tiktok.api("/post/publish/status/fetch/", {"publish_id": "pub_1"})
        self.assertEqual(json.loads(stdout.getvalue()), {"ok": False, "error": "TikTok API error spam_risk: blocked"})

    def test_empty_file_is_rejected_before_network(self):
        with tempfile.NamedTemporaryFile(suffix=".mp4") as video, patch("urllib.request.urlopen") as mocked, self.assertRaises(
            SystemExit
        ), redirect_stdout(io.StringIO()):
            tiktok.upload_file(video.name)
        mocked.assert_not_called()


if __name__ == "__main__":
    unittest.main()
