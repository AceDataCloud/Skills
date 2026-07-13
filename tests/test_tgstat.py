from __future__ import annotations

import importlib.util
import io
import json
import os
import pathlib
import unittest
from contextlib import redirect_stdout
from unittest import mock


SCRIPT = pathlib.Path(__file__).parents[1] / "skills" / "tgstat" / "scripts" / "tgstat.py"
SPEC = importlib.util.spec_from_file_location("tgstat_skill", SCRIPT)
assert SPEC and SPEC.loader
tgstat = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tgstat)


class TGStatParserTests(unittest.TestCase):
    def test_skill_has_one_frontmatter_block(self) -> None:
        skill = SCRIPT.parent.parent / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        self.assertEqual(text.count("\n---\n"), 1)

    def test_parses_channel_and_chat_ranking_cards(self) -> None:
        html = """
        <div class="card peer-item-row mb-2 ribbon-box border">
          <div class="ribbon ribbon-secondary">#4</div>
          <a href="https://tgstat.com/channel/@ai_news/stat">
            <div class="text-truncate font-16 text-dark mt-n1">AI News</div>
            <span class="border rounded bg-light px-1">Technologies</span>
          </a>
          <h4>12 345</h4><div class="text-muted text-truncate">subscribers</div>
          <h4>146.7k</h4><div class="text-muted text-truncate">1 post reach</div>
        </div>
        <div class="card peer-item-row mb-2 ribbon-box border">
          <a href="https://uk.tgstat.com/chat/@ai_builders/stat">
            <div class="text-truncate font-16 text-dark mt-n1">AI Builders</div>
          </a>
          <h4>3.1k</h4><div class="text-muted text-truncate">MAU</div>
        </div>
        """
        items = tgstat.parse_rankings_html(html)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["rank"], 4)
        self.assertEqual(items[0]["username"], "@ai_news")
        self.assertEqual(items[0]["metrics"]["subscribers"], 12345)
        self.assertEqual(items[0]["metrics"]["1_post_reach"], 146700)
        self.assertEqual(items[1]["type"], "chat")
        self.assertEqual(items[1]["metrics"]["mau"], 3100)

    def test_public_search_builds_channel_and_chat_web_queries(self) -> None:
        queries = tgstat._web_queries("Claude API", "all", "English", "USA")
        self.assertEqual(len(queries), 4)
        self.assertIn('site:tgstat.com/chat/ "Claude API" English USA', queries)
        self.assertIn('site:t.me/ "Claude API" channel English USA', queries)

    def test_rejects_non_tgstat_public_host(self) -> None:
        with self.assertRaises(tgstat.TGStatError):
            tgstat._public_base("https://example.com")

    def test_ranking_parser_rejects_lookalike_host(self) -> None:
        html = """
        <div class="card peer-item-row">
          <a href="https://tgstat.com.evil.test/channel/@ai_news/stat">
            <div class="text-truncate font-16 text-dark">AI News</div>
          </a>
        </div>
        """
        self.assertEqual(tgstat.parse_rankings_html(html), [])

    def test_rejects_invite_message_and_non_entity_links(self) -> None:
        targets = (
            "https://t.me/+secretInvite",
            "https://t.me/ai_news/42",
            "https://tgstat.com/ratings/channels",
            "http://t.me/ai_news",
            "@../ratings",
        )
        for target in targets:
            with self.subTest(target=target), self.assertRaises(tgstat.TGStatError):
                tgstat._normalize_target(target)

    def test_rejects_cross_host_redirect_before_following(self) -> None:
        handler = tgstat.SafeRedirectHandler("tgstat.com")
        request = tgstat.urllib.request.Request("https://tgstat.com/channel/@durov/stat")
        with self.assertRaises(tgstat.TGStatError):
            handler.redirect_request(request, None, 302, "Found", {}, "https://example.com/steal")

    def test_numeric_ids_are_normalized_for_public_pages(self) -> None:
        self.assertEqual(tgstat._normalize_target("53248")[0], "id53248")
        self.assertEqual(tgstat._normalize_target("id53248")[0], "id53248")

    def test_decodes_percent_encoded_entity_paths_once(self) -> None:
        entity = tgstat._entity_from_url("https://tgstat.com/channel/%40durov/stat")
        self.assertEqual(entity, ("channel", "@durov"))

    def test_canonicalizes_tgstat_ru_input_to_public_com_host(self) -> None:
        identifier, peer_type, url = tgstat._normalize_target("https://tgstat.ru/channel/%40durov/stat")
        self.assertEqual((identifier, peer_type), ("@durov", "channel"))
        self.assertEqual(url, "https://tgstat.com/channel/%40durov/stat")

    def test_connected_username_is_normalized(self) -> None:
        with mock.patch.dict(os.environ, {"TGSTAT_USERNAME": "durov"}, clear=True):
            self.assertEqual(tgstat._connected_username(), "@durov")

    def test_connected_username_is_required_and_must_be_public(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True), self.assertRaises(tgstat.TGStatError):
            tgstat._connected_username()
        with mock.patch.dict(os.environ, {"TGSTAT_USERNAME": "https://t.me/+private"}, clear=True), self.assertRaises(
            tgstat.TGStatError
        ):
            tgstat._connected_username()

    def test_profile_reports_username_without_claiming_verification(self) -> None:
        args = tgstat.build_parser().parse_args(["profile"])
        output = io.StringIO()
        with mock.patch.dict(os.environ, {"TGSTAT_USERNAME": "@durov"}, clear=True), redirect_stdout(output):
            args.func(args)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["username"], "@durov")
        self.assertFalse(payload["verified"])

    def test_info_defaults_to_connected_username(self) -> None:
        args = tgstat.build_parser().parse_args(["info"])
        with mock.patch.dict(os.environ, {"TGSTAT_USERNAME": "@durov"}, clear=True), mock.patch.object(
            tgstat, "_public_info", return_value={"status": "ok", "identifier": "@durov"}
        ) as public_info, redirect_stdout(io.StringIO()):
            args.func(args)
        self.assertEqual(public_info.call_args.args[1], "@durov")

    def test_skill_fallback_matches_runtime_bundle_layout(self) -> None:
        skill = SCRIPT.parent.parent / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        self.assertNotIn("*/skills/*/tgstat/scripts/tgstat.py", text)
        self.assertEqual(text.count("*/skills/*/scripts/tgstat.py"), 5)

    def test_ranking_interstitial_returns_web_fallback(self) -> None:
        args = tgstat.build_parser().parse_args(["rankings", "--type", "channel"])
        output = io.StringIO()
        with mock.patch.object(tgstat, "_request", return_value="<title>Authentication Required - 429</title>"), redirect_stdout(output):
            args.func(args)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["status"], "unavailable")
        self.assertTrue(payload["requires_web_fetch"])
        self.assertTrue(payload["requires_web_search"])
        self.assertIn("not an authoritative TGStat ranking", payload["limitations"])

    def test_unrecognized_detail_page_is_not_reported_as_ok(self) -> None:
        html = "<html><head><title>Just a moment...</title></head><body>Challenge</body></html>"
        result = tgstat.parse_detail_html(html, "https://tgstat.com/channel/@durov/stat")
        self.assertEqual(result["status"], "unrecognized")

    def test_parses_public_detail_metadata(self) -> None:
        html = """
        <html><head><meta property="og:title" content="AI Builders — TGStat">
        <meta property="og:description" content="Public AI developer chat"></head>
        <body><h4>8.2k</h4><div class="text-muted text-truncate">messages</div></body></html>
        """
        result = tgstat.parse_detail_html(html, "https://tgstat.com/chat/@ai_builders/stat")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["identifier"], "@ai_builders")
        self.assertEqual(result["metrics"]["messages"], 8200)


if __name__ == "__main__":
    unittest.main()