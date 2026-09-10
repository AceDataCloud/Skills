import unittest
from pathlib import Path


SKILL = Path(__file__).parents[1] / "skills" / "gpt-image-2-5" / "SKILL.md"


class GPTImage25SkillContractTests(unittest.TestCase):
    def test_official_variants_are_documented(self) -> None:
        text = SKILL.read_text()

        self.assertIn("gpt-image-2.5-flare:official", text)
        self.assertIn("gpt-image-2.5-sunburst:official", text)


if __name__ == "__main__":
    unittest.main()
