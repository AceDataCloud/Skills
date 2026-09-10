import unittest
from pathlib import Path


SKILL = Path(__file__).parents[1] / "skills" / "gpt-image-2" / "SKILL.md"


class GptImage2AsyncContractTests(unittest.TestCase):
    def test_documents_synchronous_and_asynchronous_responses(self) -> None:
        text = SKILL.read_text()
        self.assertIn("return image URL(s) directly by default, or a `task_id`", text)
        self.assertIn('An asynchronous request returns `{"task_id":"..."}` instead.', text)
        self.assertIn('POST /openai/tasks` with `{"id": "<task_id>"}`', text)


if __name__ == "__main__":
    unittest.main()
