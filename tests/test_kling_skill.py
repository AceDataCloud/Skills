from pathlib import Path
import unittest


SKILL = Path(__file__).parents[1] / "skills" / "kling-video" / "SKILL.md"


class KlingSkillContractTests(unittest.TestCase):
    def test_video_defaults_match_openapi(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertIn('| `mode` | `"std"` (default), `"pro"`, `"4k"` |', text)
        self.assertIn("| `duration` | `5` (default);", text)


if __name__ == "__main__":
    unittest.main()
