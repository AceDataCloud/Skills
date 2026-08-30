from pathlib import Path
import unittest


class SyncDocsTests(unittest.TestCase):
    def test_gpt_image_2_mentions_async_and_new_models(self):
        skill = Path(__file__).resolve().parents[1] / "skills" / "gpt-image-2" / "SKILL.md"
        text = skill.read_text(encoding="utf-8")

        self.assertIn("synchronous by default", text)
        self.assertIn("`gpt-image-2:reverse`", text)
        self.assertIn("`gpt-image-2:official`", text)
        self.assertIn("application/json", text)
        self.assertIn("multipart/form-data", text)

    def test_wan_duration_range_matches_latest_docs(self):
        skill = Path(__file__).resolve().parents[1] / "skills" / "wan-video" / "SKILL.md"
        text = skill.read_text(encoding="utf-8")

        self.assertIn("integer `2`–`30`, or `-1`", text)
        self.assertIn("Supported duration input is integer `2`–`30` or `-1`", text)


if __name__ == "__main__":
    unittest.main()
