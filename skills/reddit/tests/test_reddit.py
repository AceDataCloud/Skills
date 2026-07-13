from __future__ import annotations

import importlib.util
import io
import json
import os
import pathlib
import sys
import time
import unittest
import urllib.error
import urllib.parse
from email.message import Message
from contextlib import redirect_stdout
from unittest.mock import patch


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "reddit.py"
SPEC = importlib.util.spec_from_file_location("reddit_skill_script", SCRIPT)
reddit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = reddit
SPEC.loader.exec_module(reddit)


class FakeResponse:
    def __init__(self, payload: dict, status: int = 200):
        self.status = status
        self.payload = json.dumps(payload).encode()
        self.headers = {}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


class BrokenResponse(FakeResponse):
    def read(self):
        raise OSError("truncated response containing session-secret")


class BrokenErrorBody(io.BytesIO):
    def read(self, *_args, **_kwargs):
        raise OSError("truncated HTTP error containing session-secret")


COOKIE_JAR = json.dumps(
    [
        {"name": "reddit_session", "value": "session-secret", "domain": ".reddit.com", "path": "/"},
        {"name": "loid", "value": "loid-value", "domain": ".reddit.com", "path": "/"},
    ]
)


class RedditSkillTests(unittest.TestCase):
    def test_cookie_header_is_restricted_to_reddit(self):
        jar = reddit.parse_cookie_jar(COOKIE_JAR)
        self.assertIn("reddit_session=session-secret", reddit.cookie_header(jar, "https://www.reddit.com/api/me.json"))
        self.assertEqual("", reddit.cookie_header(jar, "https://example.com/"))

    def test_cookie_jar_rejects_missing_wrong_domain_or_empty_session(self):
        invalid_jars = [
            [{"name": "reddit_session", "value": "secret", "path": "/"}],
            [{"name": "reddit_session", "value": "secret", "domain": ".example.com", "path": "/"}],
            [{"name": "reddit_session", "value": "", "domain": ".reddit.com", "path": "/"}],
            [{"name": "reddit_session", "value": "secret; injected=yes", "domain": ".reddit.com", "path": "/"}],
            [{"name": "reddit_session", "value": {"secret": True}, "domain": ".reddit.com", "path": "/"}],
            [
                {
                    "name": "reddit_session",
                    "value": "secret",
                    "domain": ".reddit.com",
                    "path": "/",
                    "expirationDate": time.time() - 1,
                }
            ],
        ]
        for jar in invalid_jars:
            with self.subTest(jar=jar), self.assertRaises(SystemExit), redirect_stdout(io.StringIO()):
                reddit.parse_cookie_jar(json.dumps(jar))

    def test_cookie_header_respects_host_only_domain_path_secure_and_expiry(self):
        jar = reddit.parse_cookie_jar(
            json.dumps(
                [
                    {"name": "reddit_session", "value": "root", "domain": ".reddit.com", "path": "/", "secure": True},
                    {"name": "host_only", "value": "yes", "domain": "www.reddit.com", "path": "/"},
                    {
                        "name": "domain_cookie",
                        "value": "yes",
                        "domain": "reddit.com",
                        "hostOnly": False,
                        "path": "/",
                    },
                    {"name": "login_only", "value": "no", "domain": ".reddit.com", "path": "/login"},
                    {
                        "name": "expired",
                        "value": "no",
                        "domain": ".reddit.com",
                        "path": "/",
                        "expirationDate": time.time() - 1,
                    },
                ]
            )
        )
        api_header = reddit.cookie_header(jar, "https://www.reddit.com/api/me.json")
        self.assertIn("reddit_session=root", api_header)
        self.assertIn("host_only=yes", api_header)
        self.assertIn("domain_cookie=yes", api_header)
        self.assertNotIn("login_only", api_header)
        self.assertNotIn("expired", api_header)
        self.assertNotIn("host_only", reddit.cookie_header(jar, "https://old.reddit.com/api/me.json"))
        self.assertIn("domain_cookie=yes", reddit.cookie_header(jar, "https://old.reddit.com/api/me.json"))
        self.assertNotIn("reddit_session", reddit.cookie_header(jar, "http://www.reddit.com/api/me.json"))

    def test_cookie_mode_fetches_modhash_and_submits_text(self):
        responses = [
            FakeResponse({"data": {"id": "abc", "name": "tester", "modhash": "csrf-secret"}}),
            FakeResponse({"json": {"errors": [], "data": {"id": "post1", "name": "t3_post1", "url": "https://www.reddit.com/r/test/comments/post1/title/"}}}),
        ]
        with patch.dict(os.environ, {"REDDIT_COOKIES": COOKIE_JAR}, clear=True), patch.object(
            reddit, "open_request", side_effect=responses
        ) as urlopen:
            client = reddit.RedditClient.from_environment()
            result = client.submit(subreddit="test", title="Title", kind="self", text="Body")

        self.assertEqual("cookie", client.mode)
        self.assertEqual("https://www.reddit.com/r/test/comments/post1/title/", result["url"])
        me_request = urlopen.call_args_list[0].args[0]
        submit_request = urlopen.call_args_list[1].args[0]
        self.assertEqual("https://www.reddit.com/api/me.json?raw_json=1", me_request.full_url)
        self.assertIn("reddit_session=session-secret", me_request.get_header("Cookie"))
        form = urllib.parse.parse_qs(submit_request.data.decode())
        self.assertEqual(["csrf-secret"], form["uh"])
        self.assertEqual(["self"], form["kind"])
        self.assertEqual(["Body"], form["text"])

    def test_oauth_mode_uses_bearer_token(self):
        with patch.dict(os.environ, {"REDDIT_TOKEN": "oauth-secret"}, clear=True), patch(
            "reddit_skill_script.open_request",
            return_value=FakeResponse({"id": "abc", "name": "tester", "total_karma": 12}),
        ) as urlopen:
            client = reddit.RedditClient.from_environment()
            profile = client.me()

        self.assertEqual("oauth", client.mode)
        self.assertEqual("tester", profile["name"])
        request = urlopen.call_args.args[0]
        self.assertEqual("https://oauth.reddit.com/api/v1/me", request.full_url)
        self.assertEqual("Bearer oauth-secret", request.get_header("Authorization"))

    def test_dry_run_never_loads_credentials_or_calls_network(self):
        stream = io.StringIO()
        with patch.dict(os.environ, {}, clear=True), patch.object(reddit, "open_request") as urlopen, redirect_stdout(stream):
            reddit.main(["submit-text", "--subreddit", "r/test", "--title", "Title", "--text", "Body"])

        value = json.loads(stream.getvalue())
        self.assertTrue(value["dry_run"])
        self.assertEqual(4, value["text_length"])
        urlopen.assert_not_called()

    def test_confirm_is_only_recognized_as_final_argument(self):
        args, confirmed = reddit.split_confirmation(["submit-text", "--text", "--confirm", "--title", "Title"])
        self.assertFalse(confirmed)
        self.assertIn("--confirm", args)
        args, confirmed = reddit.split_confirmation(["submit-text", "--title", "Title", "--confirm"])
        self.assertTrue(confirmed)
        self.assertNotIn("--confirm", args)

    def test_rejects_cookie_jar_without_reddit_session(self):
        with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()):
            reddit.parse_cookie_jar(json.dumps([{"name": "loid", "value": "x", "domain": ".reddit.com"}]))

    def test_redirect_is_rejected_without_following(self):
        headers = Message()
        headers["Location"] = "https://example.com/steal"
        redirect = urllib.error.HTTPError(
            "https://www.reddit.com/api/me.json",
            302,
            "Found",
            headers,
            io.BytesIO(b"redirect"),
        )
        client = reddit.RedditClient("cookie", cookies=reddit.parse_cookie_jar(COOKIE_JAR))
        with patch.object(reddit, "open_request", side_effect=redirect) as open_request, self.assertRaises(
            SystemExit
        ), redirect_stdout(io.StringIO()):
            client.me()

        open_request.assert_called_once()

    def test_post_redirect_reports_unknown_outcome_without_retry_advice(self):
        headers = Message()
        headers["Location"] = "https://www.reddit.com/r/test/comments/post1/title/"
        redirect = urllib.error.HTTPError(
            "https://www.reddit.com/api/submit",
            303,
            "See Other",
            headers,
            io.BytesIO(b"redirect"),
        )
        client = reddit.RedditClient("cookie", cookies=reddit.parse_cookie_jar(COOKIE_JAR))
        client.modhash = "csrf-secret"
        stream = io.StringIO()
        with patch.object(reddit, "open_request", side_effect=redirect) as open_request, self.assertRaises(
            SystemExit
        ), redirect_stdout(stream):
            client.submit(subreddit="test", title="Title", kind="self", text="Body")

        rendered = stream.getvalue()
        self.assertIn("outcome is unknown", rendered)
        self.assertIn("Check recent submissions", rendered)
        self.assertIn("do not replay", rendered)
        self.assertNotIn("retry once", rendered)
        open_request.assert_called_once()

    def test_post_body_failures_report_unknown_outcome_without_secret_details(self):
        cases = [
            FakeResponse({}, status=200),
            FakeResponse({}, status=200),
            BrokenResponse({}),
        ]
        cases[0].payload = b"<html>session-secret</html>"
        cases[1].payload = b"not-json session-secret"
        cases.append(FakeResponse({}, status=200))
        cases[-1].payload = b"not-gzip session-secret"
        cases[-1].headers = {"Content-Encoding": "gzip"}

        for response in cases:
            client = reddit.RedditClient("cookie", cookies=reddit.parse_cookie_jar(COOKIE_JAR))
            stream = io.StringIO()
            with self.subTest(response=type(response).__name__), patch.object(
                reddit, "open_request", return_value=response
            ) as open_request, self.assertRaises(SystemExit), redirect_stdout(stream):
                client.request("POST", "/api/submit", form={"api_type": "json"})
            rendered = stream.getvalue()
            self.assertIn("outcome is unknown", rendered)
            self.assertIn("do not replay", rendered)
            self.assertNotIn("session-secret", rendered)
            open_request.assert_called_once()

    def test_post_http_error_body_read_failure_reports_unknown_outcome(self):
        error = urllib.error.HTTPError(
            "https://www.reddit.com/api/submit",
            500,
            "Internal Server Error",
            Message(),
            BrokenErrorBody(b"unreadable"),
        )
        client = reddit.RedditClient("cookie", cookies=reddit.parse_cookie_jar(COOKIE_JAR))
        stream = io.StringIO()
        with patch.object(reddit, "open_request", side_effect=error) as open_request, self.assertRaises(
            SystemExit
        ), redirect_stdout(stream):
            client.request("POST", "/api/submit", form={"api_type": "json"})

        rendered = stream.getvalue()
        self.assertIn("outcome is unknown", rendered)
        self.assertIn("Check recent submissions", rendered)
        self.assertIn("do not replay", rendered)
        self.assertNotIn("session-secret", rendered)
        open_request.assert_called_once()

    def test_authenticated_error_does_not_echo_reflected_secrets(self):
        reflected = "session-secret csrf-secret oauth-secret"
        error = urllib.error.HTTPError(
            "https://www.reddit.com/api/submit",
            500,
            "Internal Server Error",
            Message(),
            io.BytesIO(reflected.encode()),
        )
        client = reddit.RedditClient("cookie", cookies=reddit.parse_cookie_jar(COOKIE_JAR))
        client.modhash = "csrf-secret"
        stream = io.StringIO()
        with patch.object(reddit, "open_request", side_effect=error), self.assertRaises(SystemExit), redirect_stdout(
            stream
        ):
            client.submit(subreddit="test", title="Title", kind="self", text="Body")

        rendered = stream.getvalue()
        self.assertIn("HTTP 500", rendered)
        self.assertNotIn("session-secret", rendered)
        self.assertNotIn("csrf-secret", rendered)
        self.assertNotIn("oauth-secret", rendered)

    def test_application_error_does_not_echo_reflected_secrets(self):
        reflected = "session-secret csrf-secret oauth-secret"
        client = reddit.RedditClient("cookie", cookies=reddit.parse_cookie_jar(COOKIE_JAR))
        client.modhash = "csrf-secret"
        stream = io.StringIO()
        response = FakeResponse({"json": {"errors": [["BAD_REQUEST", reflected, reflected]], "data": {}}})
        with patch.object(reddit, "open_request", return_value=response), self.assertRaises(
            SystemExit
        ), redirect_stdout(stream):
            client.submit(subreddit="test", title="Title", kind="self", text="Body")

        rendered = stream.getvalue()
        self.assertIn("Reddit rejected the post", rendered)
        self.assertNotIn("session-secret", rendered)
        self.assertNotIn("csrf-secret", rendered)
        self.assertNotIn("oauth-secret", rendered)

    def test_submissions_rejects_malformed_json_shape(self):
        client = reddit.RedditClient("oauth", token="oauth-secret")
        client.username = "tester"
        for payload in (
            {},
            [],
            {"data": {}},
            {"data": {"children": [{}]}},
            {"data": {"children": [{"data": {}}]}},
        ):
            stream = io.StringIO()
            with self.subTest(payload=payload), patch.object(
                client, "request", return_value=payload
            ), self.assertRaises(SystemExit), redirect_stdout(stream):
                client.submissions(10)
            self.assertIn("malformed submissions response", stream.getvalue())
            self.assertNotIn("oauth-secret", stream.getvalue())

    def test_submissions_accepts_documented_shape(self):
        client = reddit.RedditClient("oauth", token="oauth-secret")
        client.username = "tester"
        payload = {
            "data": {
                "children": [
                    {
                        "data": {
                            "id": "post1",
                            "title": "Title",
                            "subreddit": "test",
                            "permalink": "/r/test/comments/post1/title/",
                        }
                    }
                ]
            }
        }
        with patch.object(client, "request", return_value=payload):
            self.assertEqual("post1", client.submissions(10)[0]["id"])

    def test_identity_and_post_reject_malformed_json_shapes(self):
        identity_client = reddit.RedditClient("oauth", token="oauth-secret")
        identity_stream = io.StringIO()
        with patch.object(identity_client, "request", return_value=[]), self.assertRaises(
            SystemExit
        ), redirect_stdout(identity_stream):
            identity_client.me()
        self.assertIn("malformed identity response", identity_stream.getvalue())

        post_client = reddit.RedditClient("cookie", cookies=reddit.parse_cookie_jar(COOKIE_JAR))
        post_client.modhash = "csrf-secret"
        malformed_posts = (
            {},
            {"json": {}},
            {"json": {"errors": None, "data": {"url": "https://www.reddit.com/r/test/comments/x/title/"}}},
            {"json": {"errors": [], "data": {"url": ["not", "a", "string"]}}},
            {"json": {"errors": [], "data": {"url": "https://example.com/not-reddit"}}},
        )
        for payload in malformed_posts:
            post_stream = io.StringIO()
            with self.subTest(payload=payload), patch.object(
                post_client, "request", return_value=payload
            ), self.assertRaises(SystemExit), redirect_stdout(post_stream):
                post_client.submit(subreddit="test", title="Title", kind="self", text="Body")
            self.assertIn("malformed write response", post_stream.getvalue())
            self.assertIn("outcome is unknown", post_stream.getvalue())
            self.assertIn("do not replay", post_stream.getvalue())
            self.assertNotIn("csrf-secret", post_stream.getvalue())


if __name__ == "__main__":
    unittest.main()