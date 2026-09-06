import unittest
from pathlib import Path


SKILL = Path(__file__).parents[1] / "skills" / "nano-banana-image" / "SKILL.md"


class NanoBananaSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.content = SKILL.read_text(encoding="utf-8")

    def test_parameters_include_count_and_async(self) -> None:
        self.assertIn("| `count` | integer `1`–`4` |", self.content)
        self.assertIn("| `async` | boolean |", self.content)

    def test_task_polling_and_403_gotchas_match_docs(self) -> None:
        self.assertIn('`action: "retrieve_batch"` with `ids`', self.content)
        self.assertIn("`403 forbidden` means the request/result was blocked by provider safety checks", self.content)
        self.assertIn("`nano-banana-2-lite` supports `1K` resolution only", self.content)


if __name__ == "__main__":
    unittest.main()
