import unittest
from pathlib import Path


SKILL = Path(__file__).parents[1] / "skills" / "suno-music" / "SKILL.md"


class SunoCustomModelsSkillContractTests(unittest.TestCase):
    def test_persona_is_incompatible_with_custom_models(self) -> None:
        text = SKILL.read_text()

        self.assertIn("`persona_id` cannot be used with a custom music model", text)
        self.assertIn("`artist_consistency` or `artist_consistency_vox`", text)


if __name__ == "__main__":
    unittest.main()
