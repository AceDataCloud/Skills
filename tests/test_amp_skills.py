"""Validate installable Amp service packages and their isolation contracts."""
import json
import re
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
AMP = ROOT / "platforms" / "amp"


class AmpServiceSkillTests(unittest.TestCase):
    def test_each_installable_skill_is_self_contained_and_service_scoped(self):
        folders = sorted((AMP / "skills").iterdir())
        self.assertEqual(len(folders), 5)
        for folder in folders:
            with self.subTest(skill=folder.name):
                text = (folder / "SKILL.md").read_text()
                self.assertEqual(re.search(r"^name: (.+)$", text, re.M)[1], folder.name)
                self.assertLessEqual(len(folder.name), 64)
                self.assertRegex(folder.name, r"^[a-z0-9-]+$")
                manifest = json.loads((folder / "mcp.json").read_text())
                self.assertEqual(len(manifest), 1)
                server = next(iter(manifest.values()))
                endpoint = urlparse(server["url"])
                self.assertEqual(endpoint.scheme, "https")
                self.assertTrue(endpoint.hostname.endswith(".mcp.acedata.cloud"))
                self.assertEqual(endpoint.path, "/mcp")
                self.assertEqual(server["headers"], {"Authorization": "Bearer ${ACEDATACLOUD_API_TOKEN}"})
                listing = json.loads((folder / "listing.json").read_text())
                self.assertEqual(server["includeTools"], listing["tool_names"])
                self.assertEqual(len(server["includeTools"]), len(set(server["includeTools"])))
                self.assertIn(listing["generation_tool"], server["includeTools"])
                self.assertIn(listing["poll_tool"], server["includeTools"])
                self.assertNotIn("*", "".join(server["includeTools"]))
                self.assertNotIn("command", server)
                self.assertTrue((folder / "LICENSE").is_file())
                for doc in folder.glob("*.md"):
                    for target in re.findall(r"\]\(([^)]+)\)", doc.read_text()):
                        if not target.startswith(("https://", "http://", "#")):
                            resolved = (folder / target).resolve()
                            self.assertTrue(resolved.is_relative_to(folder.resolve()), target)
                            self.assertTrue(resolved.is_file(), target)

    def test_image_packages_do_not_expose_chat_audio_or_unrelated_tools(self):
        for name in ["gpt-image-by-acedatacloud", "nano-banana-by-acedatacloud"]:
            listing = json.loads((AMP / "skills" / name / "listing.json").read_text())
            self.assertEqual(listing["category"], "image")
            for tool in listing["tool_names"]:
                self.assertNotRegex(tool, r"chat|speech|embedding|response|realtime|voice")
        listing = json.loads((AMP / "skills/gpt-image-by-acedatacloud/listing.json").read_text())
        self.assertEqual(listing["poll_argument"], "id")
        for other in ["suno", "seedance", "happyhorse", "nano-banana"]:
            listing = json.loads((AMP / "skills" / (other + "-by-acedatacloud") / "listing.json").read_text())
            self.assertEqual(listing["poll_argument"], "task_id")

    def test_every_customer_cta_has_amp_attribution_and_no_secret(self):
        seen = 0
        for doc in (AMP / "skills").glob("*/README*.md"):
            for url in re.findall(r"https://platform\.acedata\.cloud/[^)\s]+", doc.read_text()):
                query = parse_qs(urlparse(url).query)
                self.assertEqual(query.get("utm_source"), ["amp"])
                for key in ["utm_medium", "utm_campaign", "utm_content"]:
                    self.assertEqual(len(query.get(key, [])), 1)
                self.assertNotRegex(url, r"[?&](api_?key|token)=")
                seen += 1
        self.assertGreaterEqual(seen, 20)
