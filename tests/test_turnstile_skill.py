import unittest
from pathlib import Path


SKILL = Path(__file__).parents[1] / "skills" / "turnstile" / "SKILL.md"


class TurnstileSkillContractTests(unittest.TestCase):
    def test_response_timestamps_are_unix_seconds(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("Unix timestamp (seconds) when solving began", text)
        self.assertIn("Unix timestamp (seconds) when solving completed", text)
        self.assertNotIn("ISO-8601 timestamp when solving began", text)
        self.assertNotIn("ISO-8601 timestamp when solving completed", text)


if __name__ == "__main__":
    unittest.main()
