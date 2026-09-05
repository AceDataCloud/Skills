import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def skill_text(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


class DocsSyncSpecTests(unittest.TestCase):
    def test_nano_banana_documents_current_request_and_task_parameters(self) -> None:
        text = skill_text("nano-banana-image")
        self.assertIn("| `count` | integer | Number of images to generate (`1`–`4`, default `1`) |", text)
        self.assertIn("| `async` | boolean | Request asynchronous task execution |", text)
        self.assertIn('"retrieve_batch"', text)
        self.assertIn("`ids`", text)
        self.assertIn('HTTP 403 with `success: false` and `error.code: "forbidden"`', text)

    def test_ai_chat_glm_examples_include_current_model(self) -> None:
        text = skill_text("ai-chat")
        self.assertIn("| GLM | `glm-5.3`, `glm-5.2`", text)


if __name__ == "__main__":
    unittest.main()
