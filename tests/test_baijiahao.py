import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request


SCRIPT = Path(__file__).resolve().parents[1] / "skills/baijiahao/scripts/baijiahao.py"
spec = importlib.util.spec_from_file_location("baijiahao", SCRIPT)
client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)
COOKIE = {"name": "BDUSS", "value": "cookie-secret", "domain": ".baidu.com", "path": "/"}
ACCOUNT = '{"errno":0,"data":{"user":{"userid":"123","name":"Author"}}}'
TOKEN_PAGE = '<script>window.__BJH__INIT__AUTH__ = "token-secret";</script>'


class BaijiahaoTests(unittest.TestCase):
    def test_dry_run_never_loads_credentials_or_accesses_network(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "article.html"
            path.write_text("<p>Text 😀</p>")
            output = io.StringIO()
            with patch.object(client, "load_cookies", side_effect=AssertionError("credentials")), \
                    patch.object(client.Client, "request", side_effect=AssertionError("network")), \
                    contextlib.redirect_stdout(output):
                result = client.main(["draft", "--title", "Title", "--content-file", str(path)])
            self.assertEqual(result, 0)
            value = json.loads(output.getvalue())
            self.assertTrue(value["dry_run"])
            self.assertFalse(value["published"])
            self.assertEqual(value["payload"]["content"], "<p>Text 😀</p>")
            self.assertEqual(value["payload"]["len"], "14")  # UTF-16 code units

    def test_confirm_is_only_valid_as_final_argument(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit), \
                patch.object(client.Client, "request", side_effect=AssertionError("network")):
            client.main(["draft", "--confirm", "--title", "T", "--content-file", "unused"])

    def test_confirmed_cli_saves_draft(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "article.html"
            path.write_text("<p>Approved</p>")
            with patch.dict(os.environ, {"BAIJIAHAO_COOKIES": json.dumps([COOKIE])}), \
                    patch.object(client.Client, "request", side_effect=[ACCOUNT, TOKEN_PAGE,
                        'bjhdraft({"errno":0,"ret":{"article_id":"987"}})']) as request, \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(client.main(["draft", "--title", "T", "--content-file", str(path), "--confirm"]), 0)
            result = json.loads(output.getvalue())
            self.assertEqual(result["status"], "draft")
            self.assertFalse(result["published"])
            self.assertEqual(result["draft_id"], "987")
            self.assertEqual(request.call_count, 3)
            self.assertEqual(request.call_args.kwargs["token"], "token-secret")
            self.assertEqual(request.call_args.kwargs["fields"]["activity_list"], "[]")
            self.assertNotIn("secret", output.getvalue())

    def test_cookie_domain_path_host_only_and_expiry(self):
        jar = [COOKIE, {**COOKIE, "name": "editor", "path": "/builder"},
               {**COOKIE, "name": "expired", "expirationDate": 1},
               {**COOKIE, "name": "host", "hostOnly": True},
               {**COOKIE, "name": "evil", "domain": "baidu.com.evil.test"},
               {**COOKIE, "name": "broad", "domain": ".com"},
               {**COOKIE, "name": "nodomain", "domain": ""}]
        self.assertEqual(client.cookie_header(jar, client.ORIGIN + "/builder/rc/edit"),
                         "editor=cookie-secret; BDUSS=cookie-secret")
        self.assertEqual(client.cookie_header(jar, client.ORIGIN + "/builder-other"), "BDUSS=cookie-secret")
        self.assertEqual(client.cookie_header(jar, client.ORIGIN + "/pcui/article/save"), "BDUSS=cookie-secret")

    def test_off_origin_cookie_use_refused(self):
        for url in ("http://baijiahao.baidu.com/", "https://evil.test/", "https://baijiahao.baidu.com.evil.test/"):
            with self.subTest(url=url), self.assertRaises(client.DraftError):
                client.cookie_header([COOKIE], url)

    def test_cookie_errors_never_echo_values(self):
        for cookie in ({**COOKIE, "name": "x\r\nsecret"}, {**COOKIE, "value": "secret\r\n"},
                       {**COOKIE, "value": "secret;other=1"}, {**COOKIE, "value": "秘密"}):
            with self.subTest(cookie=cookie), self.assertRaises(client.DraftError) as error:
                client.cookie_header([cookie], client.ORIGIN + "/")
            self.assertNotIn("secret", str(error.exception))

    def test_bad_cookie_json_is_sanitized(self):
        for value in ("secret{", '{"token":"secret"}', '["secret"]', "[]"):
            with patch.dict(os.environ, {"BAIJIAHAO_COOKIES": value}), self.assertRaises(client.DraftError) as error:
                client.load_cookies()
            self.assertNotIn("secret", str(error.exception))

    def test_json_and_jsonp(self):
        for text in ('{"errno":0}', ' bjhdraft({"errno":0}) ', 'bjhdraft({"errno":0});'):
            self.assertEqual(client.parse_response(text), {"errno": 0})
        for text in ('bjhdraft({}); evil()', 'other({})', '<html>secret</html>', '[]'):
            with self.assertRaises(client.DraftError) as error:
                client.parse_response(text)
            self.assertNotIn("secret", str(error.exception))

    def test_failed_identity_prevents_write(self):
        for response in ('{"errno":1}', '{"errno":0,"data":[]}', '{"errno":0,"data":{"user":{}}}'):
            with patch.object(client.Client, "request", return_value=response) as request, self.assertRaises(client.DraftError):
                client.Client([COOKIE]).draft(client.draft_fields("T", "<p>B</p>"))
            self.assertEqual(request.call_count, 1)

    def test_editor_without_token_prevents_write(self):
        with patch.object(client.Client, "request", side_effect=[ACCOUNT, '<html>login cookie-secret</html>']) as request, \
                self.assertRaises(client.DraftError) as error:
            client.Client([COOKIE]).draft(client.draft_fields("T", "<p>B</p>"))
        self.assertEqual(request.call_count, 2)
        self.assertNotIn("secret", str(error.exception))

    def test_save_ambiguity_is_not_retried_or_reported_as_success(self):
        for response in ('{"errno":0,"ret":{}}', '{"errno":1,"errmsg":"token-secret"}',
                         '{"errno":0,"ret":{"article_id":true}}',
                         '{"errno":0,"ret":{"article_id":"../wrong"}}', '<html>token-secret</html>'):
            with self.subTest(response=response), \
                    patch.object(client.Client, "request", side_effect=[ACCOUNT, TOKEN_PAGE, response]) as request, \
                    self.assertRaises(client.DraftError) as error:
                client.Client([COOKIE]).draft(client.draft_fields("T", "<p>B</p>"))
            self.assertEqual(request.call_count, 3)
            self.assertIn("before retrying", str(error.exception))
            self.assertNotIn("secret", str(error.exception))

    def test_timeout_after_save_is_unknown_and_never_retried(self):
        with patch.object(client.Client, "request", side_effect=[ACCOUNT, TOKEN_PAGE, client.DraftError("request failed")]) as request, \
                self.assertRaises(client.DraftError) as error:
            client.Client([COOKIE]).draft(client.draft_fields("T", "B"))
        self.assertEqual(request.call_count, 3)
        self.assertIn("unknown", str(error.exception))

    def test_transport_refuses_redirects_and_does_not_log_bodies(self):
        instance = client.Client([COOKIE])
        redirect = next(h for h in instance.opener.handlers if isinstance(h, client.NoRedirect))
        req = urllib.request.Request(client.ORIGIN)
        self.assertIsNone(redirect.redirect_request(req, None, 302, "Found", {}, "https://evil.test"))
        error = urllib.error.HTTPError(client.ORIGIN, 403, "cookie-secret", {}, io.BytesIO(b"token-secret"))
        with patch.object(instance.opener, "open", side_effect=error) as opened, self.assertRaises(client.DraftError) as caught:
            instance.request("/builder/app/appinfo")
        self.assertNotIn("secret", str(caught.exception))
        request = opened.call_args.args[0]
        self.assertEqual(request.get_header("Cookie"), "BDUSS=cookie-secret")
        self.assertNotIn("Cookie", request.headers)

    def test_empty_and_oversize_content_rejected(self):
        for title, body in ((" ", "x"), ("T", " "), ("T", "x" * (client.MAX_BYTES + 1))):
            with self.assertRaises(client.DraftError):
                client.draft_fields(title, body)


if __name__ == "__main__":
    unittest.main()
