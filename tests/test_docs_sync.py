import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class DocsSyncTests(unittest.TestCase):
    def test_glm_5_3_is_documented(self) -> None:
        skill = (ROOT / "skills" / "ai-chat" / "SKILL.md").read_text()

        self.assertIn("`glm-5.3`", skill)

    def test_qwen_image_cost_response_is_documented(self) -> None:
        skill = (ROOT / "skills" / "qwen-image" / "SKILL.md").read_text()

        self.assertIn("`cost`", skill)
        self.assertTrue(
            all(f"`{field}`" in skill for field in ("amount", "currency", "list_amount"))
        )


if __name__ == "__main__":
    unittest.main()
