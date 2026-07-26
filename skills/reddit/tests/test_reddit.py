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

    def test_normalize_thing_id_accepts_fullnames_and_permalinks(self):
        self.assertEqual("t3_abc123", reddit.normalize_thing_id("t3_abc123"))
        self.assertEqual("t1_def456", reddit.normalize_thing_id("t1_def456"))
        self.assertEqual(
            "t3_1r9yrtn",
            reddit.normalize_thing_id("https://www.reddit.com/r/SunoAI/comments/1r9yrtn/reliable_alternative/"),
        )
        self.assertEqual(
            "t1_def456",
            reddit.normalize_thing_id("https://www.reddit.com/r/test/comments/abc123/some_slug/def456/"),
        )

    def test_normalize_thing_id_rejects_non_reddit_and_malformed(self):
        for value in [
            "https://evil.example.com/r/test/comments/abc123/x/",
            "t9_abc123",
            "not-a-thing",
            "https://www.reddit.com/r/test/",
            # Only comments (t1_) and posts (t3_) can be replied to.
            "t2_abc123",
            "t4_abc123",
            "t5_abc123",
            "t6_abc123",
        ]:
            stream = io.StringIO()
            with self.subTest(value=value), self.assertRaises(SystemExit), redirect_stdout(stream):
                reddit.normalize_thing_id(value)

    def test_comment_dry_run_never_calls_network(self):
        stream = io.StringIO()
        with patch.dict(os.environ, {}, clear=True), patch.object(reddit, "open_request") as urlopen, redirect_stdout(
            stream
        ):
            reddit.main(["comment", "--parent", "t3_abc123", "--body", "Body"])

        value = json.loads(stream.getvalue())
        self.assertTrue(value["dry_run"])
        self.assertEqual("t3_abc123", value["parent"])
        self.assertEqual(4, value["body_length"])
        urlopen.assert_not_called()

    def test_comment_body_containing_confirm_cannot_trigger_a_write(self):
        stream = io.StringIO()
        with patch.dict(os.environ, {"REDDIT_COOKIES": COOKIE_JAR}, clear=True), patch.object(
            reddit, "open_request"
        ) as urlopen, redirect_stdout(stream):
            reddit.main(["comment", "--parent", "t3_abc123", "--body", "please --confirm this"])

        self.assertTrue(json.loads(stream.getvalue())["dry_run"])
        urlopen.assert_not_called()

    def test_cookie_mode_comment_sends_modhash_and_returns_permalink(self):
        responses = [
            FakeResponse({"data": {"id": "abc", "name": "tester", "modhash": "csrf-secret"}}),
            FakeResponse(
                {
                    "json": {
                        "errors": [],
                        "data": {
                            "things": [
                                {
                                    "data": {
                                        "id": "c1",
                                        "name": "t1_c1",
                                        "permalink": "/r/test/comments/post1/title/c1/",
                                    }
                                }
                            ]
                        },
                    }
                }
            ),
        ]
        with patch.dict(os.environ, {"REDDIT_COOKIES": COOKIE_JAR}, clear=True), patch.object(
            reddit, "open_request", side_effect=responses
        ) as urlopen:
            client = reddit.RedditClient.from_environment()
            result = client.comment(parent="t3_post1", body="Reply body")

        self.assertTrue(result["commented"])
        self.assertEqual("https://www.reddit.com/r/test/comments/post1/title/c1/", result["url"])
        comment_request = urlopen.call_args_list[1].args[0]
        self.assertEqual("https://www.reddit.com/api/comment", comment_request.full_url)
        form = urllib.parse.parse_qs(comment_request.data.decode())
        self.assertEqual(["csrf-secret"], form["uh"])
        self.assertEqual(["t3_post1"], form["thing_id"])
        self.assertEqual(["Reply body"], form["text"])

    def test_comment_rejection_and_malformed_shapes_hide_authenticated_details(self):
        client = reddit.RedditClient("cookie", cookies=reddit.parse_cookie_jar(COOKIE_JAR))
        client.modhash = "csrf-secret"
        payloads = [
            {"json": {"errors": [["RATELIMIT", "you are doing that too much csrf-secret", None]]}},
            {"json": {"errors": []}},
            {"json": {"errors": [], "data": {"things": []}}},
            # No id at all -> genuinely unknown outcome.
            {"json": {"errors": [], "data": {"things": [{"data": {"body": "x"}}]}}},
        ]
        for payload in payloads:
            stream = io.StringIO()
            with self.subTest(payload=payload), patch.object(
                client, "request", return_value=payload
            ), self.assertRaises(SystemExit), redirect_stdout(stream):
                client.comment(parent="t3_post1", body="Body")
            self.assertNotIn("csrf-secret", stream.getvalue())

    def test_comment_without_permalink_is_a_success_not_an_unknown_outcome(self):
        """Cookie mode often omits permalink; an id means Reddit created the comment."""
        client = reddit.RedditClient("cookie", cookies=reddit.parse_cookie_jar(COOKIE_JAR))
        client.modhash = "csrf-secret"
        payload = {
            "json": {"errors": [], "data": {"things": [{"data": {"id": "nabc123", "name": "t1_nabc123"}}]}}
        }
        with patch.object(client, "request", return_value=payload):
            result = client.comment(parent="t3_1v711cj", body="Looks good")

        self.assertTrue(result["commented"])
        self.assertEqual("nabc123", result["id"])
        self.assertEqual("https://www.reddit.com/comments/1v711cj/_/nabc123/", result["url"])

    def test_comments_fails_closed_on_drifted_shape(self):
        """A silently-empty list would read as 'the write did not land' -> duplicate reply."""
        client = reddit.RedditClient("cookie", cookies=reddit.parse_cookie_jar(COOKIE_JAR))
        client.username = "tester"
        drifted = {"data": {"children": [{"kind": "t1", "comment": {"id": "c1", "body": "x"}}]}}
        stream = io.StringIO()
        with patch.object(client, "request", return_value=drifted), self.assertRaises(
            SystemExit
        ), redirect_stdout(stream):
            client.comments(10)
        self.assertIn("malformed comments response", stream.getvalue())

    def test_comments_accepts_documented_shape_and_survives_odd_body(self):
        client = reddit.RedditClient("cookie", cookies=reddit.parse_cookie_jar(COOKIE_JAR))
        client.username = "tester"
        payload = {
            "data": {
                "children": [
                    {
                        "kind": "t1",
                        "data": {
                            "id": "c1",
                            "body": "Looks good",
                            "permalink": "/r/test/comments/p1/t/c1/",
                            "link_title": "Test",
                            "subreddit": "test",
                        },
                    }
                ]
            }
        }
        with patch.object(client, "request", return_value=payload):
            items = client.comments(10)
        self.assertEqual(1, len(items))
        formatted = reddit.format_comment(items[0])
        self.assertEqual("Looks good", formatted["body"])
        self.assertEqual("https://www.reddit.com/r/test/comments/p1/t/c1/", formatted["url"])

    def test_reply_to_a_comment_derives_a_real_permalink_from_link_id(self):
        client = reddit.RedditClient("cookie", cookies=reddit.parse_cookie_jar(COOKIE_JAR))
        client.modhash = "csrf-secret"
        payload = {
            "json": {
                "errors": [],
                "data": {"things": [{"data": {"id": "nc2", "name": "t1_nc2", "link_id": "t3_1v711cj"}}]},
            }
        }
        with patch.object(client, "request", return_value=payload):
            result = client.comment(parent="t1_parent1", body="Reply")
        self.assertEqual("https://www.reddit.com/comments/1v711cj/_/nc2/", result["url"])

    def test_derive_comment_url_rejects_ids_that_could_escape_reddit(self):
        for thread, comment_id in [
            ("abc123", "x/../../../@evil.example.com"),
            ("../../evil", "c1"),
            ("abc123", ""),
        ]:
            stream = io.StringIO()
            with self.subTest(thread=thread, comment_id=comment_id), self.assertRaises(
                SystemExit
            ), redirect_stdout(stream):
                reddit.derive_comment_url(thread, comment_id)

    def test_comment_accepts_permalink_only_and_name_only_responses(self):
        """Proof of creation in any form must never be reported as unknown."""
        client = reddit.RedditClient("cookie", cookies=reddit.parse_cookie_jar(COOKIE_JAR))
        client.modhash = "csrf-secret"

        # permalink but no id
        payload = {"json": {"errors": [], "data": {"things": [
            {"data": {"name": "t1_nabc12", "permalink": "/r/test/comments/1v711cj/slug/nabc12/"}}]}}}
        with patch.object(client, "request", return_value=payload):
            result = client.comment(parent="t3_1v711cj", body="B")
        self.assertTrue(result["commented"])
        self.assertEqual("https://www.reddit.com/r/test/comments/1v711cj/slug/nabc12/", result["url"])

        # name but no id and no permalink
        payload = {"json": {"errors": [], "data": {"things": [
            {"data": {"name": "t1_nabc12", "link_id": "t3_1v711cj"}}]}}}
        with patch.object(client, "request", return_value=payload):
            result = client.comment(parent="t1_x1", body="B")
        self.assertTrue(result["commented"])
        self.assertEqual("https://www.reddit.com/comments/1v711cj/_/nabc12/", result["url"])

    def test_comment_with_unknown_thread_still_reports_success(self):
        """We hold the id, so it was created; a 'failure' here would invite a duplicate."""
        client = reddit.RedditClient("cookie", cookies=reddit.parse_cookie_jar(COOKIE_JAR))
        client.modhash = "csrf-secret"
        payload = {"json": {"errors": [], "data": {"things": [{"data": {"id": "nc9", "name": "t1_nc9"}}]}}}
        with patch.object(client, "request", return_value=payload):
            result = client.comment(parent="t1_parent1", body="Reply")
        self.assertTrue(result["commented"])
        self.assertEqual("nc9", result["id"])
        self.assertIsNone(result["url"])
        self.assertIn("do not resend", result["note"])

    def test_valid_comment_data_rejects_bad_types_but_allows_null_permalink(self):
        self.assertTrue(reddit.valid_comment_data({"id": "c1", "body": "x", "permalink": None}))
        self.assertTrue(reddit.valid_comment_data({"id": "c1", "body": "[deleted]"}))
        self.assertFalse(reddit.valid_comment_data({"id": "c1", "body": {"nested": 1}}))
        self.assertFalse(reddit.valid_comment_data({"id": "c1", "body": 123}))
        self.assertFalse(reddit.valid_comment_data({"id": "", "body": "x"}))
        self.assertFalse(reddit.valid_comment_data({"body": "x"}))

    def test_comments_listing_survives_a_null_permalink_sibling(self):
        client = reddit.RedditClient("cookie", cookies=reddit.parse_cookie_jar(COOKIE_JAR))
        client.username = "tester"
        payload = {"data": {"children": [
            {"data": {"id": "c1", "body": "Looks good", "permalink": "/r/test/comments/p1/t/c1/"}},
            {"data": {"id": "c2", "body": "older", "permalink": None}},
        ]}}
        with patch.object(client, "request", return_value=payload):
            items = client.comments(10)
        self.assertEqual(2, len(items))
        self.assertIsNone(reddit.format_comment(items[1])["url"])

    def test_comment_body_limits_are_enforced(self):
        for body in ["", "   ", "x" * 10_001]:
            stream = io.StringIO()
            with self.subTest(body=len(body)), self.assertRaises(SystemExit), redirect_stdout(stream):
                reddit.validate_comment_body(body)

    def test_search_returns_fullnames_for_reply_targets(self):
        payload = {
            "data": {
                "children": [
                    {
                        "data": {
                            "id": "p1",
                            "name": "t3_p1",
                            "title": "Looking for a Suno API",
                            "subreddit": "SunoAI",
                            "permalink": "/r/SunoAI/comments/p1/looking/",
                            "selftext": "x" * 900,
                        }
                    },
                    {"data": {"id": "bad"}},
                ]
            }
        }
        client = reddit.RedditClient("cookie", cookies=reddit.parse_cookie_jar(COOKIE_JAR))
        with patch.object(client, "request", return_value=payload):
            hits = client.search(query="suno api", limit=5)

        self.assertEqual(1, len(hits))
        formatted = reddit.format_search_hit(hits[0])
        self.assertEqual("t3_p1", formatted["fullname"])
        self.assertEqual("https://www.reddit.com/r/SunoAI/comments/p1/looking/", formatted["url"])
        self.assertEqual(500, len(formatted["selftext_excerpt"]))

    def test_search_defaults_to_relevance_because_new_ignores_keywords(self):
        """Reddit's `new` sort returns recent posts that need not match the query."""
        client = reddit.RedditClient("cookie", cookies=reddit.parse_cookie_jar(COOKIE_JAR))
        with patch.object(client, "request", return_value={"data": {"children": []}}) as request:
            client.search(query="suno api")
        self.assertEqual("relevance", request.call_args.kwargs["query"]["sort"])

        stream = io.StringIO()
        with patch.dict(os.environ, {"REDDIT_COOKIES": COOKIE_JAR}, clear=True), patch.object(
            reddit.RedditClient, "search", return_value=[]
        ) as search, redirect_stdout(stream):
            reddit.main(["search", "--query", "suno api"])
        self.assertEqual("relevance", search.call_args.kwargs["sort"])

    def test_search_is_a_read_and_rejects_malformed_shape(self):
        client = reddit.RedditClient("cookie", cookies=reddit.parse_cookie_jar(COOKIE_JAR))
        stream = io.StringIO()
        with patch.object(client, "request", return_value={"data": {}}), self.assertRaises(
            SystemExit
        ), redirect_stdout(stream):
            client.search(query="suno api")
        self.assertIn("malformed search response", stream.getvalue())


    def test_comment_write_failures_never_advise_checking_submissions(self):
        """A comment never appears in `submissions`; that advice would cause a duplicate reply."""
        client = reddit.RedditClient("cookie", cookies=reddit.parse_cookie_jar(COOKIE_JAR))
        client.modhash = "csrf-secret"

        # Malformed shape.
        stream = io.StringIO()
        with patch.object(client, "request", return_value={"json": {"errors": []}}), self.assertRaises(
            SystemExit
        ), redirect_stdout(stream):
            client.comment(parent="t3_post1", body="Body")
        self.assertIn("comment outcome is unknown", stream.getvalue())
        self.assertIn("parent thread", stream.getvalue())
        self.assertNotIn("recent submissions", stream.getvalue())

        # Transport failure inside request().
        stream = io.StringIO()
        with patch.object(
            reddit, "open_request", side_effect=urllib.error.URLError("boom")
        ), self.assertRaises(SystemExit), redirect_stdout(stream):
            client.request("POST", "/api/comment", form={"text": "x"}, write_kind="comment")
        self.assertIn("comment outcome is unknown", stream.getvalue())
        self.assertNotIn("recent submissions", stream.getvalue())

    def test_post_write_failures_still_advise_checking_submissions(self):
        client = reddit.RedditClient("cookie", cookies=reddit.parse_cookie_jar(COOKIE_JAR))
        stream = io.StringIO()
        with patch.object(
            reddit, "open_request", side_effect=urllib.error.URLError("boom")
        ), self.assertRaises(SystemExit), redirect_stdout(stream):
            client.request("POST", "/api/submit", form={"title": "x"})
        self.assertIn("post outcome is unknown", stream.getvalue())
        self.assertIn("recent submissions", stream.getvalue())


if __name__ == "__main__":
    unittest.main()