import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("clawhub_catalog", ROOT / "scripts/build_clawhub_catalog.py")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)
CATALOG = json.loads((ROOT / "clawhub/catalog.json").read_text())


class NativeCatalogTests(unittest.TestCase):
    def test_five_independent_services_have_unique_existing_source(self):
        services = CATALOG["services"]
        self.assertEqual({s["id"] for s in services}, {"suno", "seedance", "happyhorse", "gpt-image", "nano-banana"})
        self.assertEqual(len({s["source"] for s in services}), 5)
        self.assertEqual(len({s["slug"] for s in services}), 5)
        for service in services:
            self.assertTrue((ROOT / service["source"] / "SKILL.md").is_file())
            self.assertTrue(service["display_name"].endswith(" by Ace Data Cloud"))
            self.assertEqual(service["categories"], ["creative"])
            self.assertLessEqual(len(service["topics"]), 5)
            self.assertNotIn("official", service["topics"])

    def test_bundles_work_standalone_with_native_key_and_original_api(self):
        with tempfile.TemporaryDirectory() as temp:
            for service in CATALOG["services"]:
                original = (ROOT / service["source"] / "SKILL.md").read_bytes()
                result = builder.build(ROOT, service, Path(temp))
                target = Path(result["bundle"])
                text = (target / "SKILL.md").read_text()
                self.assertIn("primaryEnv", text)
                self.assertIn('"env": ["ACEDATACLOUD_API_TOKEN"]', text)
                self.assertIn('"bins": ["curl"]', text)
                self.assertIn('"apiKey": "YOUR_ACE_SERVICE_API_KEY"', text)
                self.assertIn('"' + result["source_name"] + '": {', text)
                self.assertIn("openclaw skills install @acedatacloud/" + service["slug"], text)
                self.assertNotIn("(../", text)
                self.assertNotIn("Continue until\n> `response.data[].video_url` appears", text)
                self.assertIn("same ID", text)
                self.assertIn("sandbox", text)
                self.assertIn("not an official integration", text)
                self.assertEqual((ROOT / service["source"] / "SKILL.md").read_bytes(), original)
                # Canonical curl examples, methods and billing-sensitive payloads remain exact.
                source_blocks = re.findall(r"```(?:bash|json)\n(.*?)```", original.decode(), re.S)
                for block in source_blocks:
                    self.assertIn(block, text)
                for lang in ("README.md", "README.zh-CN.md"):
                    readme = (target / lang).read_text()
                    self.assertIn("get-api-key-en.png", readme)
                    self.assertIn("create-api-key-en.png", readme)
                    self.assertIn("platform-", readme)
                    self.assertIn("General application", readme)
                    self.assertIn("429", readme)
                self.assertIn("gpt-image-2.5-flare", text) if service["id"] == "gpt-image" else None

    def test_links_match_current_backend_contract_without_new_source(self):
        for service in CATALOG["services"]:
            for placement in ("signup", "api_key", "pricing"):
                tags = parse_qs(urlparse(builder.link(service, placement)).query)
                self.assertEqual(set(tags), {"utm_source", "utm_medium", "utm_campaign", "utm_content"})
                self.assertEqual(tags["utm_source"], ["agent_skill"])
                self.assertEqual(tags["utm_medium"], ["referral"])
                self.assertEqual(tags["utm_campaign"], ["evergreen"])
                self.assertIn("_clawhub_", tags["utm_content"][0])
                for values in tags.values():
                    self.assertRegex(values[0], r"^[a-z0-9][a-z0-9_.-]{0,95}$")

    def test_build_does_not_overwrite_reviewed_output(self):
        with tempfile.TemporaryDirectory() as temp:
            builder.build(ROOT, CATALOG["services"][0], Path(temp))
            with self.assertRaises(FileExistsError):
                builder.build(ROOT, CATALOG["services"][0], Path(temp))


if __name__ == "__main__":
    unittest.main()
