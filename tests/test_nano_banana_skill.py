import unittest
from pathlib import Path


SKILL = Path(__file__).parents[1] / "skills" / "nano-banana-image" / "SKILL.md"


def body() -> str:
    return SKILL.read_text()


class NanoBananaSkillContractTests(unittest.TestCase):
    def test_parameters_include_count_and_async(self) -> None:
        text = body()
        self.assertIn("| `count` | integer `1`-`4` |", text)
        self.assertIn("| `async` | boolean |", text)

    def test_gotchas_cover_batch_task_polling(self) -> None:
        self.assertIn('"ids":[...],"action":"retrieve_batch"', body())

    def test_gotchas_cover_lite_resolution_limit(self) -> None:
        self.assertIn("`nano-banana-2-lite` only supports `1K` resolution", body())


if __name__ == "__main__":
    unittest.main()
