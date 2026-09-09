from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / "mcp-packages.json").read_text())


def table_rows(path: Path) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for line in path.read_text().splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not re.fullmatch(r"[a-z0-9-]+", cells[0]):
            continue
        package_match = re.search(r"pip install ([a-z0-9-]+)", line)
        endpoint_match = re.search(r"https://[a-z0-9.-]+/mcp", line)
        if package_match and endpoint_match:
            rows[cells[0]] = (package_match.group(1), endpoint_match.group(0))
    return rows


class McpPackageCatalogTest(unittest.TestCase):
    def test_catalog_is_unique_and_points_to_public_mcp_endpoints(self) -> None:
        self.assertEqual(CATALOG["schema_version"], 1)
        self.assertEqual(CATALOG["verified_at"], "2026-09-10")
        mappings = CATALOG["mappings"]
        self.assertEqual(len({item["skill"] for item in mappings}), len(mappings))
        self.assertEqual(len({item["package"] for item in mappings}), len(mappings))
        for item in mappings:
            self.assertTrue((ROOT / "skills" / item["skill"] / "SKILL.md").is_file())
            parsed = urlparse(item["endpoint"])
            self.assertEqual(parsed.scheme, "https")
            self.assertEqual(parsed.path, "/mcp")
            self.assertTrue(
                parsed.hostname and parsed.hostname.endswith(".acedata.cloud")
            )

    def test_root_and_shared_tables_match_the_catalog(self) -> None:
        expected = {
            item["skill"]: (item["package"], item["endpoint"])
            for item in CATALOG["mappings"]
        }
        self.assertEqual(table_rows(ROOT / "README.md"), expected)
        self.assertEqual(
            table_rows(ROOT / "skills" / "_shared" / "mcp-servers.md"), expected
        )

    def test_corrected_skills_name_the_canonical_package(self) -> None:
        expected = {
            "seedream-image": "mcp-seedream-pro",
            "nano-banana-image": "mcp-nanobanana-pro",
            "kling-video": "mcp-kling",
        }
        for skill, package in expected.items():
            content = (ROOT / "skills" / skill / "SKILL.md").read_text()
            self.assertIn(f"pip install {package}", content)

    def test_known_invalid_package_identities_do_not_reappear(self) -> None:
        public_docs = "\n".join(
            path.read_text()
            for path in (
                ROOT / "README.md",
                ROOT / "skills" / "_shared" / "mcp-servers.md",
                ROOT / "skills" / "seedream-image" / "SKILL.md",
                ROOT / "skills" / "nano-banana-image" / "SKILL.md",
            )
        )
        self.assertNotRegex(public_docs, r"\bmcp-seedream(?!-pro)")
        self.assertNotIn("mcp-nano-banana", public_docs)


if __name__ == "__main__":
    unittest.main()
