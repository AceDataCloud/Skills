from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import pathlib
import sys
import unittest
import unittest.mock
import urllib.error

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "yuque.py"
SPEC = importlib.util.spec_from_file_location("yuque_skill_script", SCRIPT)
yuque = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = yuque
SPEC.loader.exec_module(yuque)


COOKIES = [
    {"name": "yuque_ctoken", "value": "CTOKEN", "domain": ".yuque.com"},
    {"name": "_yuque_session", "value": "SESSION", "domain": ".yuque.com"},
]


def run(argv, env):
    """Run main() with a patched environ and captured stdout."""
    buffer = io.StringIO()
    code = 0
    with unittest.mock.patch.dict(yuque.os.environ, env, clear=True):
        with contextlib.redirect_stdout(buffer):
            try:
                yuque.main(argv)
            except SystemExit as exc:  # die() path
                code = exc.code
    return code, json.loads(buffer.getvalue())


class ModeSelection(unittest.TestCase):
    def test_token_wins_when_both_credentials_are_present(self):
        with unittest.mock.patch.dict(
            yuque.os.environ,
            {"YUQUE_TOKEN": "t", "YUQUE_COOKIES": json.dumps(COOKIES)},
            clear=True,
        ):
            self.assertEqual(yuque.YuqueClient.from_environment().mode, "token")

    def test_cookie_is_the_fallback(self):
        with unittest.mock.patch.dict(
            yuque.os.environ, {"YUQUE_COOKIES": json.dumps(COOKIES)}, clear=True
        ):
            self.assertEqual(yuque.YuqueClient.from_environment().mode, "cookie")

    def test_no_credential_dies_with_a_reconnect_hint(self):
        code, payload = run(["whoami"], {})
        self.assertEqual(code, 1)
        self.assertIn("connections", payload["error"])

    def test_cookie_jar_without_ctoken_is_rejected(self):
        jar = [c for c in COOKIES if c["name"] != "yuque_ctoken"]
        code, payload = run(["whoami"], {"YUQUE_COOKIES": json.dumps(jar)})
        self.assertEqual(code, 1)
        self.assertIn("yuque_ctoken", payload["error"])


class CookieScoping(unittest.TestCase):
    def test_jar_is_not_sent_off_domain(self):
        self.assertEqual(yuque.cookie_header(COOKIES, "https://evil.example/x"), "")

    def test_jar_is_sent_to_yuque(self):
        header = yuque.cookie_header(COOKIES, "https://www.yuque.com/api/mine")
        self.assertIn("_yuque_session=SESSION", header)

    def test_domainless_cookie_is_not_leaked_to_an_unrelated_host(self):
        jar = COOKIES + [{"name": "loose", "value": "L"}]
        self.assertEqual(yuque.cookie_header(jar, "https://evil.example/x"), "")

    def test_a_lookalike_suffix_host_is_not_matched(self):
        self.assertEqual(yuque.cookie_header(COOKIES, "https://notyuque.com/api"), "")


class WriteGating(unittest.TestCase):
    def test_create_without_confirm_is_a_dry_run(self):
        code, payload = run(
            ["create", "1", "--title", "T", "--content", "body"],
            {"YUQUE_COOKIES": json.dumps(COOKIES)},
        )
        self.assertEqual(code, 0)
        self.assertTrue(payload["dry_run"])

    def test_confirm_is_only_honored_as_the_last_argument(self):
        # A real --confirm argv element that is NOT last must not confirm.
        argv = ["create", "1", "--confirm", "--title", "T", "--content", "b"]
        self.assertEqual(yuque.split_confirmation(argv), (argv, False))

    def test_confirm_as_the_last_argument_does_confirm(self):
        clean, confirmed = yuque.split_confirmation(["create", "1", "--confirm"])
        self.assertTrue(confirmed)
        self.assertEqual(clean, ["create", "1"])

    def test_a_body_containing_the_flag_is_not_a_confirmation(self):
        code, payload = run(
            ["create", "1", "--title", "T", "--content", "please --confirm this"],
            {"YUQUE_COOKIES": json.dumps(COOKIES)},
        )
        self.assertEqual(code, 0)
        self.assertTrue(payload["dry_run"])

    def test_create_defaults_to_private(self):
        code, payload = run(
            ["create", "1", "--title", "T", "--content", "b"],
            {"YUQUE_COOKIES": json.dumps(COOKIES)},
        )
        self.assertEqual(payload["visibility"], "private")


class TokenOnlyCommands(unittest.TestCase):
    def test_update_is_refused_on_a_cookie_connection(self):
        code, payload = run(
            ["update", "1", "9", "--title", "T", "--content", "b", "--confirm"],
            {"YUQUE_COOKIES": json.dumps(COOKIES)},
        )
        self.assertEqual(code, 1)
        self.assertIn("personal token", payload["error"])

    def test_delete_is_refused_on_a_cookie_connection(self):
        code, payload = run(
            ["delete", "1", "9", "--confirm"], {"YUQUE_COOKIES": json.dumps(COOKIES)}
        )
        self.assertEqual(code, 1)
        self.assertIn("personal token", payload["error"])


class RequestShape(unittest.TestCase):
    """Capture the outgoing request instead of calling 语雀."""

    def _capture(self, mode_env, method, path, **kwargs):
        seen = {}

        class Opener:
            def open(self, request, timeout=None):
                seen["request"] = request
                raise urllib.error.HTTPError(
                    request.full_url, 401, "Unauthorized", {}, None
                )

        with unittest.mock.patch.dict(yuque.os.environ, mode_env, clear=True):
            client = yuque.YuqueClient.from_environment()
        client._opener = Opener()
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit):
                client.request(method, path, **kwargs)
        return seen["request"]

    def test_cookie_mode_sends_csrf_origin_and_referer(self):
        request = self._capture({"YUQUE_COOKIES": json.dumps(COOKIES)}, "GET", "/mine")
        self.assertEqual(request.full_url, "https://www.yuque.com/api/mine")
        self.assertEqual(request.get_header("X-csrf-token"), "CTOKEN")
        # 语雀's CSRF layer rejects writes without these two.
        self.assertEqual(request.get_header("Origin"), "https://www.yuque.com")
        self.assertTrue(request.get_header("Referer"))

    def test_cookie_is_unredirected_so_it_is_dropped_on_a_30x(self):
        request = self._capture({"YUQUE_COOKIES": json.dumps(COOKIES)}, "GET", "/mine")
        self.assertIn("Cookie", request.unredirected_hdrs)
        self.assertNotIn("Cookie", request.headers)

    def test_token_mode_uses_the_open_api_and_auth_header(self):
        request = self._capture({"YUQUE_TOKEN": "TK"}, "GET", "/user")
        self.assertEqual(request.full_url, "https://www.yuque.com/api/v2/user")
        self.assertEqual(request.get_header("X-auth-token"), "TK")
        self.assertIsNone(request.get_header("X-csrf-token"))

    def test_cookie_create_sends_markdown_without_a_convert_round_trip(self):
        request = self._capture(
            {"YUQUE_COOKIES": json.dumps(COOKIES)},
            "POST",
            "/docs",
            body={"book_id": 1, "format": "markdown", "body": "# hi"},
            write=True,
        )
        payload = json.loads(request.data)
        self.assertEqual(payload["format"], "markdown")


class RedirectHandling(unittest.TestCase):
    def test_redirects_are_refused(self):
        handler = yuque.NoRedirectHandler()
        self.assertIsNone(
            handler.redirect_request(None, None, 302, "Found", {}, "https://evil.example")
        )

    def test_the_no_redirect_handler_is_actually_installed(self):
        # Cookie is unredirected, but x-csrf-token is NOT — urllib copies every
        # other header onto a redirected request, so only refusing the redirect
        # keeps the CSRF token off a foreign host.
        with unittest.mock.patch.dict(
            yuque.os.environ, {"YUQUE_COOKIES": json.dumps(COOKIES)}, clear=True
        ):
            client = yuque.YuqueClient.from_environment()
        self.assertTrue(
            any(isinstance(h, yuque.NoRedirectHandler) for h in client._opener.handlers),
            "default opener must install NoRedirectHandler",
        )

    def test_a_30x_on_a_write_reports_an_unknown_outcome(self):
        class Opener:
            def open(self, request, timeout=None):
                raise urllib.error.HTTPError(
                    request.full_url, 302, "Found", {}, None
                )

        with unittest.mock.patch.dict(
            yuque.os.environ, {"YUQUE_COOKIES": json.dumps(COOKIES)}, clear=True
        ):
            client = yuque.YuqueClient.from_environment()
        client._opener = Opener()
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            with self.assertRaises(SystemExit):
                client.request("POST", "/docs", body={}, write=True)
        error = json.loads(buffer.getvalue())["error"]
        self.assertIn("UNKNOWN", error)


class BookIdResolution(unittest.TestCase):
    """`_book_id` turns a repo reference into the numeric id the internal API needs."""

    def _client(self, books):
        with unittest.mock.patch.dict(
            yuque.os.environ, {"YUQUE_COOKIES": json.dumps(COOKIES)}, clear=True
        ):
            client = yuque.YuqueClient.from_environment()
        client._books_cache = books
        return client

    def _expect_die(self, fn, *args):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            with self.assertRaises(SystemExit):
                fn(*args)
        return json.loads(buffer.getvalue())["error"]

    def test_non_ascii_digits_do_not_crash(self):
        # str.isdigit() is Unicode-aware but int() is not; a traceback would
        # break the JSON-only output contract.
        error = self._expect_die(self._client([])._book_id, "²")
        self.assertIn("Could not resolve", error)

    def test_a_malformed_book_id_is_skipped_not_fatal(self):
        client = self._client(
            [{"slug": "bad", "target_id": "not-a-number"}, {"slug": "blog", "target_id": 42}]
        )
        self.assertEqual(client._book_id("alice/blog"), 42)

    def test_an_ambiguous_slug_is_refused_rather_than_guessed(self):
        # Writing to the wrong knowledge base would be a silent wrong result.
        client = self._client(
            [{"slug": "blog", "target_id": 111}, {"slug": "blog", "target_id": 222}]
        )
        error = self._expect_die(client._book_id, "alice/blog")
        self.assertIn("matches 2", error)

    def test_books_are_fetched_once_per_run(self):
        client = self._client(None)
        calls = []

        def fake_repos(login=None):
            calls.append(1)
            return [{"slug": "blog", "target_id": 7}]

        client.repos = fake_repos
        client._book_id("a/blog")
        client._book_id("a/blog")
        self.assertEqual(len(calls), 1)


class OutputShape(unittest.TestCase):
    def test_repos_reports_target_id_as_the_repo_id(self):
        # The common-used record's own `id` is not the book id.
        formatted = yuque.format_repo({"id": 55555555, "target_id": 12345, "slug": "blog"})
        self.assertEqual(formatted["repo_id"], 12345)

    def test_repos_derives_a_namespace_from_the_owner_login(self):
        formatted = yuque.format_repo(
            {"target_id": 1, "slug": "blog", "user": {"login": "alice"}}
        )
        self.assertEqual(formatted["namespace"], "alice/blog")

    def test_cookie_mode_create_returns_a_real_url(self):
        # SKILL.md requires a real URL for publish_artifact; a null would
        # invite the model to invent one.
        client = self._cookie_client()
        client._book_meta[9] = {"slug": "blog", "user": {"login": "alice"}}
        url = client.doc_url(9, {"id": 1, "slug": "abc123"})
        self.assertEqual(url, "https://www.yuque.com/alice/blog/abc123")

    def test_doc_url_is_none_rather_than_wrong_when_the_book_is_unknown(self):
        client = self._cookie_client()
        self.assertIsNone(client.doc_url(9, {"id": 1, "slug": "abc123"}))

    def _cookie_client(self):
        with unittest.mock.patch.dict(
            yuque.os.environ, {"YUQUE_COOKIES": json.dumps(COOKIES)}, clear=True
        ):
            return yuque.YuqueClient.from_environment()


if __name__ == "__main__":
    unittest.main()
