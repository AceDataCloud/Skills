"""Contracts for independently installed Claude service plugins."""

import json
import re
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


ROOT = Path(__file__).parents[1]
PLUGIN_ROOT = ROOT / "claude-plugins"
EXPECTED = {
    "suno": "suno",
    "seedance": "seedance",
    "happyhorse": "happyhorse",
    "gpt-image": "openai",
    "nano-banana": "nanobanana",
}


class ClaudeServicePluginTests(unittest.TestCase):
    def test_each_service_is_an_independent_self_contained_install(self):
        marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
        entries = {entry["name"]: entry for entry in marketplace["plugins"]}
        self.assertEqual(len(entries), len(marketplace["plugins"]))
        for service in EXPECTED:
            slug = f"{service}-by-ace-data-cloud"
            entry = entries[slug]
            folder = (ROOT / entry["source"]).resolve()
            self.assertEqual(folder, PLUGIN_ROOT / slug)
            manifest = json.loads((folder / ".claude-plugin/plugin.json").read_text())
            self.assertEqual(manifest["name"], slug)
            self.assertEqual(manifest["author"]["name"], "Ace Data Cloud")
            self.assertTrue(manifest["displayName"].endswith(" by Ace Data Cloud"))
            self.assertEqual(entry["displayName"], manifest["displayName"])
            self.assertTrue((folder / manifest["icon"]).is_file())
            self.assertNotIn("skills", entry)  # Do not combine conflicting manifests.
            skills = list((folder / "skills").glob("*/SKILL.md"))
            self.assertEqual(len(skills), 1)
            self.assertEqual(skills[0].parent.name, service)
            for relative in ["README.md", "readme/README_zh_Hans.md", "LICENSE"]:
                self.assertTrue((folder / relative).is_file(), relative)
            # The installed plugin must not need symlinks outside its copied payload.
            self.assertFalse(any(path.is_symlink() for path in folder.rglob("*")))

    def test_tokens_are_explicit_sensitive_options_for_the_own_service(self):
        for service, host in EXPECTED.items():
            folder = PLUGIN_ROOT / f"{service}-by-ace-data-cloud"
            manifest = json.loads((folder / ".claude-plugin/plugin.json").read_text())
            self.assertEqual(set(manifest["mcpServers"]), {service})
            token = manifest["userConfig"]["api_token"]
            self.assertTrue(token["sensitive"])
            self.assertTrue(token["required"])
            self.assertNotIn("default", token)
            server = manifest["mcpServers"][service]
            if service == "gpt-image":
                self.assertEqual(server["command"], "uvx")
                self.assertEqual(
                    server["args"],
                    ["mcp-openai-pro==2026.10.19.3", "--profile", "gpt-image"],
                )
                self.assertEqual(
                    server["env"],
                    {"ACEDATACLOUD_API_TOKEN": "${user_config.api_token}"},
                )
                self.assertNotIn("url", server)
                self.assertNotIn("headers", server)
            else:
                self.assertEqual(server["type"], "http")
                self.assertEqual(server["url"], f"https://{host}.mcp.acedata.cloud/mcp")
                self.assertEqual(
                    server["headers"], {"Authorization": "Bearer ${user_config.api_token}"}
                )
            self.assertNotIn("hooks", manifest)
            self.assertNotIn("dependencies", manifest)
            self.assertFalse((folder / "hooks").exists())
            self.assertFalse((folder / "bin").exists())
            text = "\n".join(path.read_text() for path in folder.rglob("*.md"))
            self.assertNotIn("$ANTHROPIC_AUTH_TOKEN", text)
            self.assertNotIn("$ANTHROPIC_API_KEY", text)

    def test_guides_and_image_references_survive_plugin_copy(self):
        for service in EXPECTED:
            folder = PLUGIN_ROOT / f"{service}-by-ace-data-cloud"
            for doc in folder.rglob("*.md"):
                for target in re.findall(r"\]\(([^)]+)\)", doc.read_text()):
                    if target.startswith(("https://", "http://", "mailto:", "#")):
                        continue
                    resolved = (doc.parent / target.split("#")[0]).resolve()
                    self.assertTrue(resolved.is_relative_to(folder), (doc, target))
                    self.assertTrue(resolved.is_file(), (doc, target))
            for name in ["get-api-key-en.png", "create-api-key-en.png"]:
                self.assertTrue((folder / "assets" / name).read_bytes().startswith(b"\x89PNG"))

    def test_signup_key_and_price_links_use_current_supported_attribution(self):
        for service in EXPECTED:
            folder = PLUGIN_ROOT / f"{service}-by-ace-data-cloud"
            for doc in [folder / "README.md", folder / "readme/README_zh_Hans.md"]:
                links = re.findall(r"\]\((https://platform\.acedata\.cloud[^)]+)\)", doc.read_text())
                tagged = [url for url in links if "utm_source=" in url]
                self.assertGreaterEqual(len(tagged), 3)
                for url in tagged:
                    query = parse_qs(urlsplit(url).query)
                    self.assertEqual(query["utm_source"], ["github"])
                    self.assertEqual(query["utm_medium"], ["referral"])
                    self.assertEqual(query["utm_campaign"], ["evergreen"])
                    self.assertRegex(query["utm_content"][0], r"^[a-z0-9][a-z0-9_.-]{0,95}$")

    def test_directory_submission_is_an_explicit_unmet_gate(self):
        packet = json.loads((PLUGIN_ROOT / "submission/catalog.json").read_text())
        self.assertEqual(packet["submission_state"], "not submitted")
        self.assertEqual(len(packet["plugins"]), 5)
        for entry in packet["plugins"]:
            self.assertIn("policy exception", entry["unverified"])
            self.assertEqual(len(entry["prompts"]), 3)
            self.assertTrue((ROOT / entry["source_folder"] / ".claude-plugin/plugin.json").is_file())


if __name__ == "__main__":
    unittest.main()
