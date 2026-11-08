"""Offline wire-contract, standalone packaging and failure-handling tests.

These mocks do not assert that a third-party account can currently publish.
"""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
common_spec = importlib.util.spec_from_file_location(
    "publishing_http", ROOT / "skills/_shared/publishing_http.py"
)
http = importlib.util.module_from_spec(common_spec)
sys.modules["publishing_http"] = http
common_spec.loader.exec_module(http)
SLUGS = (
    "jianshu",
    "netease",
    "infoq",
    "tencentcloud-community",
    "aliyun-community",
    "volcengine-community",
    "modelscope",
    "sohu",
    "douban",
)
MODULES = {}
for slug in SLUGS:
    spec = importlib.util.spec_from_file_location(
        slug.replace("-", "_"),
        ROOT / "skills" / slug / "scripts" / (slug.replace("-", "_") + ".py"),
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    MODULES[slug] = module


def options(**extra):
    return SimpleNamespace(
        title="Test title", format="text", notebook_id="7", account_id="8", **extra
    )


class HTTPTransportTests(unittest.TestCase):
    def client(self, cookies=None):
        return http.HTTP(
            "TEST_COOKIES",
            ["https://writer.example.com"],
            "https://writer.example.com/",
            cookies=cookies
            or [
                {
                    "name": "session",
                    "value": "cookie-secret",
                    "domain": ".example.com",
                    "path": "/",
                }
            ],
        )

    def test_domain_path_host_only_and_expiry(self):
        jar = [
            {"name": "ok", "value": "v", "domain": ".example.com", "path": "/"},
            {
                "name": "specific",
                "value": "v",
                "domain": ".example.com",
                "path": "/writer",
            },
            {"name": "wrong", "value": "v", "domain": "example.com.evil", "path": "/"},
            {"name": "broad", "value": "v", "domain": ".com", "path": "/"},
            {
                "name": "expired",
                "value": "v",
                "domain": ".example.com",
                "expirationDate": 1,
            },
            {"name": "host", "value": "v", "domain": "example.com", "hostOnly": True},
            {"name": "empty", "value": "v"},
        ]
        client = self.client(jar)
        self.assertEqual(
            [x[1] for x in client.matching("https://writer.example.com/writer/a")],
            ["specific", "ok"],
        )
        self.assertEqual(
            [x[1] for x in client.matching("https://writer.example.com/writer-other")],
            ["ok"],
        )
        with self.assertRaises(http.Error):
            client.matching("https://elsewhere.example.com/writer")
        with self.assertRaises(http.Error):
            client.matching("http://writer.example.com/writer")

    def test_invalid_cookie_never_leaks(self):
        for value in ("cookie-secret\n", "cookie-secret;other=1", "秘密"):
            with self.subTest(value=value), self.assertRaises(http.Error) as caught:
                self.client(
                    [{"name": "s", "value": value, "domain": ".example.com"}]
                ).matching("https://writer.example.com/")
            self.assertNotIn(value, str(caught.exception))

    def test_redirect_is_refused_and_http_errors_are_sanitized(self):
        client = self.client()
        self.assertIsNone(
            http.NoRedirect().redirect_request(
                None, None, 302, "", {}, "https://evil.test"
            )
        )
        error = urllib.error.HTTPError(
            "https://writer.example.com",
            429,
            "token-secret",
            {},
            io.BytesIO(b"cookie-secret"),
        )
        with (
            patch.object(client.opener, "open", side_effect=error) as opened,
            self.assertRaises(http.Error) as caught,
        ):
            client.request(
                "https://writer.example.com/save", method="POST", data={"x": 1}
            )
        self.assertEqual(opened.call_count, 1)
        self.assertNotIn("secret", str(caught.exception))
        self.assertIn("429", str(caught.exception))
        req = opened.call_args.args[0]
        self.assertNotIn("Cookie", req.headers)
        self.assertEqual(req.get_header("Cookie"), "session=cookie-secret")

    def test_csrf_uses_scoped_cookie_and_no_value_in_error(self):
        with self.assertRaises(http.Error) as caught:
            self.client().cookie("missing", "https://writer.example.com/")
        self.assertNotIn("cookie-secret", str(caught.exception))
        with self.assertRaises(http.Error):
            self.client().request(
                "https://writer.example.com/",
                headers={"X-CSRF-TOKEN": "token-secret\r\n"},
            )


class PublisherContractTests(unittest.TestCase):
    def test_every_bundle_runs_standalone(self):
        canonical = (ROOT / "skills/_shared/publishing_http.py").read_bytes()
        for slug in SLUGS:
            with self.subTest(slug=slug):
                directory = ROOT / "skills" / slug / "scripts"
                self.assertEqual(
                    (directory / "publishing_http.py").read_bytes(), canonical
                )
                result = subprocess.run(
                    [
                        sys.executable,
                        str(directory / (slug.replace("-", "_") + ".py")),
                        "--help",
                    ],
                    capture_output=True,
                    text=True,
                    cwd="/tmp",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("publish-public", result.stdout)

    def test_all_dry_runs_are_offline_and_do_not_load_secrets(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "content"
            path.write_text("First paragraph\n第二段 😀")
            for slug, module in MODULES.items():
                adapter = module.Adapter()
                with (
                    self.subTest(slug=slug),
                    patch.object(
                        http.HTTP, "jar", side_effect=AssertionError("secret lookup")
                    ),
                    patch.object(
                        http.HTTP, "request", side_effect=AssertionError("network")
                    ),
                    contextlib.redirect_stdout(io.StringIO()) as output,
                ):
                    args = [
                        adapter.command,
                        "--title",
                        "Title",
                        "--content-file",
                        str(path),
                    ]
                    if slug == "jianshu":
                        args += ["--notebook-id", "7"]
                    if slug == "sohu":
                        args += ["--account-id", "8"]
                    self.assertEqual(http.run(module.Adapter, args), 0)
                    self.assertTrue(json.loads(output.getvalue())["dry_run"])

    def test_nonfinal_confirm_is_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            http.run(
                MODULES["jianshu"].Adapter,
                ["draft", "--confirm", "--title", "T", "--content-file", "x"],
            )

    def test_single_write_platform_contracts(self):
        cases = {
            "netease": (
                {"code": 1, "data": {"wemediaId": "1", "tname": "Author"}},
                {"code": 1, "data": "docId=42"},
                "/wemedia/article/status/api/publishV2.do",
            ),
            "aliyun-community": (
                {"success": True, "data": {"uccId": "1", "nickname": "Author"}},
                {"success": True, "data": {"aid": 42}},
                "/developer/api/articleDraft/putDraft",
            ),
            "volcengine-community": (
                {"err_no": 0, "data": {"xid": "1", "name": "Author"}},
                {"err_no": 0, "data": {"article_info": {"draft_id": "42"}}},
                "/proxy_tech_api/v1/draft/publish",
            ),
            "tencentcloud-community": (
                {"code": 0, "data": {"userId": 1, "nickName": "Author"}},
                {"draftId": 42},
                "/developer/api/article/addArticleDraft",
            ),
            "modelscope": (
                {"Code": 200, "Success": True, "Data": {"Name": "Author"}},
                {"Code": 200, "Success": True, "Data": {"Id": 42}},
                "/api/v1/articles",
            ),
            "sohu": (
                {
                    "code": 2000000,
                    "data": {"data": [{"accounts": [{"id": 8, "nickName": "Author"}]}]},
                },
                {"success": True, "data": 42},
                "/mpbp/bp/news/v4/news/draft/v2",
            ),
        }
        for slug, (profile, response, endpoint) in cases.items():
            with self.subTest(slug=slug):
                adapter = MODULES[slug].Adapter()
                opts = options()
                opts.format = adapter.formats[0]
                payload = adapter.prepare(opts, "Full article 😀")
                with (
                    patch.object(
                        adapter.http, "request", side_effect=[profile, response]
                    ) as call,
                    patch.object(adapter.http, "cookie", return_value="csrf-secret"),
                ):
                    account = adapter.whoami()
                    result = adapter.write(opts, payload, account)
                self.assertEqual(call.call_count, 2)
                self.assertIn(endpoint, call.call_args.args[0])
                self.assertEqual(result["status"], "draft")
                self.assertFalse(result["published"])
                self.assertFalse(result["readback_verified"])
                if slug == "netease":
                    self.assertEqual(
                        call.call_args.kwargs["form"]["operation"], "saveDraft"
                    )
                if slug == "modelscope":
                    self.assertFalse(result["title_saved"])
                self.assertNotIn("csrf-secret", json.dumps(result))

    def test_jianshu_updates_original_note_and_preserves_partial_id(self):
        for final in (None, http.Error("body failed")):
            adapter = MODULES["jianshu"].Adapter()
            opts = options()
            payload = adapter.prepare(opts, "All body")
            with patch.object(
                adapter.http,
                "request",
                side_effect=[
                    [{"id": 7, "name": "Notebook"}],
                    {"id": 42, "autosave_control": 4},
                    final,
                ],
            ) as call:
                if final is None:
                    result = adapter.write(opts, payload, {"name": "Author"})
                    self.assertTrue(result["body_saved"])
                    self.assertEqual(
                        call.call_args.kwargs["data"]["autosave_control"], 5
                    )
                    self.assertEqual(
                        call.call_args.kwargs["data"]["content"], "All body"
                    )
                else:
                    with self.assertRaises(http.Error) as error:
                        adapter.write(opts, payload, {"name": "Author"})
                    self.assertEqual(error.exception.result["draft_id"], "42")
                    self.assertFalse(error.exception.result["body_saved"])
                self.assertEqual(call.call_count, 3)

    def test_infoq_author_gate_and_partial_write(self):
        adapter = MODULES["infoq"].Adapter()
        opts = options()
        payload = adapter.prepare(opts, "Body")
        with patch.object(adapter.http, "request", side_effect=AssertionError("write")):
            with self.assertRaises(http.Error):
                adapter.write(opts, payload, {"is_author": 1})
        with patch.object(
            adapter.http,
            "request",
            side_effect=[{"code": 0, "data": {"id": 42}}, {"code": 1}],
        ) as call:
            with self.assertRaises(http.Error) as error:
                adapter.write(opts, payload, {"is_author": 2})
            self.assertEqual(error.exception.result["draft_id"], "42")
            self.assertFalse(error.exception.result["body_saved"])
            self.assertEqual(call.call_count, 2)

    def test_sohu_never_selects_another_subaccount(self):
        adapter = MODULES["sohu"].Adapter()
        opts = options()
        payload = adapter.prepare(opts, "Body")
        with patch.object(adapter.http, "request", side_effect=AssertionError("write")):
            with self.assertRaises(http.Error):
                adapter.write(opts, payload, {"accounts": [{"id": "9"}]})

    def test_douban_private_post_is_not_a_draft(self):
        adapter = MODULES["douban"].Adapter()
        opts = options()
        payload = adapter.prepare(opts, "Private note")
        self.assertEqual(payload["accessible"], "private")
        self.assertEqual(adapter.command, "post-private")
        with (
            patch.object(
                adapter.http,
                "request",
                return_value={"id": "42", "url": "https://www.douban.com/topic/42/"},
            ),
            patch.object(adapter.http, "cookie", return_value="csrf-secret"),
        ):
            result = adapter.write(opts, payload, {"user_id": "1"})
        self.assertEqual(result["status"], "private_post")
        self.assertFalse(result["published_publicly"])

    def test_native_formats_preserve_text_and_reject_wrong_roots(self):
        for slug in ("modelscope", "infoq", "douban"):
            adapter = MODULES[slug].Adapter()
            opts = options()
            payload = adapter.prepare(opts, "First\nEmoji 😀")
            encoded = payload.get("content") or payload.get("ContentDraft")
            self.assertIn("Emoji 😀", encoded)
            opts.format = "native"
            with self.assertRaises(http.Error):
                adapter.prepare(opts, '{"wrong":true}')

    def test_http_aliases_are_injectable_by_current_runtime(self):
        for slug in SLUGS:
            adapter = MODULES[slug].Adapter()
            self.assertRegex(adapter.http.env, r"^[A-Z0-9]+_COOKIES$")

    def test_http_write_failures_do_not_fall_back_or_retry(self):
        for slug in (
            "netease",
            "aliyun-community",
            "volcengine-community",
            "tencentcloud-community",
            "modelscope",
            "sohu",
            "douban",
        ):
            adapter = MODULES[slug].Adapter()
            opts = options()
            opts.format = adapter.formats[0]
            payload = adapter.prepare(opts, "Body")
            adapter.account = {}
            account = {"user_id": "1", "accounts": [{"id": "8"}]}
            with (
                self.subTest(slug=slug),
                patch.object(
                    adapter.http, "request", side_effect=http.Error("transport failed")
                ) as call,
                patch.object(adapter.http, "cookie", return_value="csrf-secret"),
                self.assertRaises(http.Error),
            ):
                adapter.write(opts, payload, account)
            self.assertEqual(call.call_count, 1)


if __name__ == "__main__":
    unittest.main()
