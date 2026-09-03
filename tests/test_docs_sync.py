import unittest
from pathlib import Path


SKILLS = Path(__file__).parents[1] / "skills"


class DocsSyncContractTests(unittest.TestCase):
    def test_suno_replace_section_result_modes_are_documented(self) -> None:
        text = (SKILLS / "suno-music" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`replace_section_result_mode`", text)
        self.assertIn('`"full_song"`, `"candidates"`', text)

    def test_seedance_reference_task_type_is_documented(self) -> None:
        text = (SKILLS / "seedance-video" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('`"reference"`', text)
        self.assertIn("`auto`, `reference`, `edit`, `extend`", text)


if __name__ == "__main__":
    unittest.main()
