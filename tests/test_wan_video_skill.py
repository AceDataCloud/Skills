import unittest
from pathlib import Path


SKILL = Path(__file__).parents[1] / "skills" / "wan-video" / "SKILL.md"


def body() -> str:
    return SKILL.read_text(encoding="utf-8")


class WanVideoSkillContractTests(unittest.TestCase):
    def test_parameters_cover_wan3_and_async_fields(self) -> None:
        text = body()
        self.assertIn('"wan3.0-video"', text)
        self.assertIn("| `ratio` | No |", text)
        self.assertIn("| `media` | Wan 3 |", text)
        self.assertIn("| `async` | No | boolean | Return task immediately", text)

    def test_duration_notes_match_wan26_and_wan3_ranges(self) -> None:
        text = body()
        self.assertIn("Wan 2.6 durations are 5, 10, or 15 seconds", text)
        self.assertIn("Wan 3 supports 2–30 seconds or `-1` auto duration", text)


if __name__ == "__main__":
    unittest.main()
