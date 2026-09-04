import unittest
from pathlib import Path


SKILL = Path(__file__).parents[1] / "skills" / "suno-music" / "SKILL.md"


class SunoSkillContractTests(unittest.TestCase):
    def test_auxiliary_endpoints_include_mp3(self) -> None:
        self.assertIn("| `/suno/mp3` | POST | Convert to MP3 format |", SKILL.read_text(encoding="utf-8"))

    def test_upload_and_lyric_prompt_parameters_match_openapi(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("optional `mode` = `standard`/`enhanced`, `name`, `callback_url`", text)
        self.assertIn("| `lyric_prompt` | string |", text)


if __name__ == "__main__":
    unittest.main()
