from pathlib import Path
import unittest


SKILL = Path(__file__).parents[1] / "skills" / "suno-music" / "SKILL.md"


class SunoMusicSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.content = SKILL.read_text(encoding="utf-8")

    def test_documents_current_v6_models(self) -> None:
        for model in ("chirp-v6", "chirp-v6-wild", "chirp-v6-mini"):
            self.assertIn(f"`{model}`", self.content)

    def test_recommends_current_default_model(self) -> None:
        self.assertIn('"model": "chirp-v6"', self.content)


if __name__ == "__main__":
    unittest.main()
