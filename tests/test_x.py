from __future__ import annotations

import asyncio
import importlib.util
import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace


SCRIPT = Path(__file__).parents[1] / "skills" / "x" / "scripts" / "x.py"
SPEC = importlib.util.spec_from_file_location("x_skill", SCRIPT)
assert SPEC and SPEC.loader
x = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(x)


def user(user_id: str = "4807296432", screen_name: str = "GermeyAce") -> SimpleNamespace:
    return SimpleNamespace(id=user_id, screen_name=screen_name, name="Germey Ace")


def tweet(tweet_id: str, *, media: bool) -> SimpleNamespace:
    return SimpleNamespace(id=tweet_id, text=f"tweet {tweet_id}", media=[object()] if media else [])


def run_payload(coroutine) -> dict:
    output = io.StringIO()
    with redirect_stdout(output):
        asyncio.run(coroutine)
    return json.loads(output.getvalue())


def run_error(coroutine) -> dict:
    output = io.StringIO()
    with redirect_stdout(output), unittest.TestCase().assertRaises(SystemExit):
        asyncio.run(coroutine)
    return json.loads(output.getvalue())


class XSkillTests(unittest.TestCase):
    def test_whoami_expect_uses_authenticated_settings_without_user_by_id(self) -> None:
        class V11:
            async def settings(self):
                return {"screen_name": "GermeyAce"}, None

        class Client:
            v11 = V11()

            async def get_user_by_screen_name(self, screen_name):
                self_test.assertEqual(screen_name, "GermeyAce")
                return user()

            async def get_user_by_id(self, _user_id):
                raise AssertionError("expected-account verification must not call UserByRestId")

        self_test = self
        result = run_payload(x.cmd_whoami(Client(), SimpleNamespace(expect="@GermeyAce")))
        self.assertEqual(result["screen_name"], "GermeyAce")
        self.assertTrue(result["identity_verified"])
        self.assertEqual(result["verification"], "authenticated_settings_matches_expected_screen_name")

    def test_whoami_expect_rejects_wrong_connected_account(self) -> None:
        class V11:
            async def settings(self):
                return {"screen_name": "OtherAccount"}, None

        class Client:
            v11 = V11()

            async def get_user_by_screen_name(self, _screen_name):
                raise AssertionError("mismatch must stop before public profile lookup")

        error = run_error(x.cmd_whoami(Client(), SimpleNamespace(expect="GermeyAce")))["error"]
        self.assertIn("@OtherAccount", error)
        self.assertIn("not @GermeyAce", error)

    def test_whoami_without_expect_uses_authenticated_settings(self) -> None:
        class V11:
            async def settings(self):
                return {"screen_name": "GermeyAce"}, None

        class Client:
            v11 = V11()

            async def get_user_by_screen_name(self, screen_name):
                return user(screen_name=screen_name)

        result = run_payload(x.cmd_whoami(Client(), SimpleNamespace(expect=None)))
        self.assertEqual(result["screen_name"], "GermeyAce")
        self.assertEqual(result["verification"], "authenticated_settings_screen_name")

    def test_user_media_falls_back_to_tweets_and_filters_media(self) -> None:
        calls = []

        class Client:
            async def get_user_by_screen_name(self, _screen_name):
                return user()

            async def get_user_tweets(self, _user_id, tweet_type, count):
                calls.append((tweet_type, count))
                if tweet_type == "Media":
                    raise KeyError("code")
                return [tweet("1", media=False), tweet("2", media=True), tweet("3", media=True)]

        result = run_payload(
            x.cmd_user_tweets(Client(), SimpleNamespace(user="GermeyAce", type="Media", limit=1))
        )
        self.assertEqual(calls, [("Media", 1), ("Tweets", 40)])
        self.assertEqual(result["type"], "Media")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["tweets"][0]["id"], "2")
        self.assertEqual(result["fallback"], "Tweets (locally filtered for media)")

    def test_user_media_does_not_hide_unrelated_errors(self) -> None:
        class Client:
            async def get_user_by_screen_name(self, _screen_name):
                return user()

            async def get_user_tweets(self, _user_id, _tweet_type, count):
                raise KeyError("unexpected")

        with self.assertRaisesRegex(KeyError, "unexpected"):
            asyncio.run(
                x.cmd_user_tweets(Client(), SimpleNamespace(user="GermeyAce", type="Media", limit=1))
            )

    def test_user_media_falls_back_on_explicit_dependency_error(self) -> None:
        class Client:
            async def get_user_by_screen_name(self, _screen_name):
                return user()

            async def get_user_tweets(self, _user_id, tweet_type, count):
                if tweet_type == "Media":
                    raise RuntimeError("Dependency: Unspecified")
                return [tweet("1", media=True)]

        result = run_payload(
            x.cmd_user_tweets(Client(), SimpleNamespace(user="GermeyAce", type="Media", limit=1))
        )
        self.assertEqual(result["fallback"], "Tweets (locally filtered for media)")

    def test_tweet_uses_batch_endpoint_without_broken_detail_fallback(self) -> None:
        class Client:
            async def get_tweets_by_ids(self, ids):
                self_test.assertEqual(ids, ["123"])
                return [tweet("123", media=False)]

            async def get_tweet_by_id(self, _tweet_id):
                raise AssertionError("TweetDetail fallback must not be called")

        self_test = self
        self.assertEqual(run_payload(x.cmd_tweet(Client(), SimpleNamespace(id="123")))["id"], "123")

    def test_tweet_reports_not_found_when_batch_is_empty(self) -> None:
        class Client:
            async def get_tweets_by_ids(self, _ids):
                return []

        error = run_error(x.cmd_tweet(Client(), SimpleNamespace(id="missing")))["error"]
        self.assertIn("not found", error)

    def test_tweet_rejects_mismatched_batch_result(self) -> None:
        class Client:
            async def get_tweets_by_ids(self, _ids):
                return [tweet("other", media=False)]

        error = run_error(x.cmd_tweet(Client(), SimpleNamespace(id="requested")))["error"]
        self.assertIn("id mismatch", error)

    def test_cloudflare_block_message_is_concise(self) -> None:
        error = RuntimeError(
            'status: 403, message: "<title>Attention Required! | Cloudflare</title>'
            'Sorry, you have been blocked Cloudflare Ray ID: '
            '<strong class="font-semibold">a1e188325e6409cc</strong> huge html"'
        )
        message = x.cloudflare_block_message(error)
        self.assertIsNotNone(message)
        self.assertIn("Cloudflare", message)
        self.assertIn("a1e188325e6409cc", message)
        self.assertNotIn("huge html", message)

    def test_whoami_parser_accepts_expected_screen_name(self) -> None:
        args = x.build_parser().parse_args(["whoami", "--expect", "GermeyAce"])
        self.assertEqual(args.expect, "GermeyAce")


if __name__ == "__main__":
    unittest.main()
