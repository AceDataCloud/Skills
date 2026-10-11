from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text()
ACQUISITION_URL = (
    "https://platform.acedata.cloud/"
    "?utm_source=github&utm_medium=repo&utm_campaign=skills-catalog"
)


class CatalogAcquisitionTest(unittest.TestCase):
    def test_platform_links_use_the_catalog_campaign(self) -> None:
        self.assertEqual(README.count(ACQUISITION_URL), 3)
        self.assertIn(f'href="{ACQUISITION_URL}"', README)
        self.assertIn(f"[AceDataCloud]({ACQUISITION_URL})", README)
        self.assertIn(f"[platform.acedata.cloud]({ACQUISITION_URL})", README)

    def test_no_unattributed_platform_root_link_remains(self) -> None:
        links = re.findall(r"(?:href=\"|\]\()(https://platform\.acedata\.cloud[^\"\s)]*)", README)
        self.assertEqual(links, [ACQUISITION_URL, ACQUISITION_URL, ACQUISITION_URL])


if __name__ == "__main__":
    unittest.main()
