import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def skill_text(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


class DocsSyncSpecTests(unittest.TestCase):
    def test_nano_banana_documents_current_request_and_task_parameters(self) -> None:
        text = skill_text("nano-banana-image")
        self.assertIn("Number of images to generate (`1`–`4`, default `1`)", text)
        self.assertIn("| `async` | boolean | Request asynchronous task execution |", text)
        self.assertIn('"retrieve_batch"', text)
        self.assertIn('error.code: "forbidden"', text)

    def test_ai_chat_glm_examples_include_current_model(self) -> None:
        self.assertIn("| GLM | `glm-5.3`, `glm-5.2`", skill_text("ai-chat"))

    def test_suno_documents_current_paid_operations(self) -> None:
        text = skill_text("suno-music")
        for detail in ("10 Credit", "0.90 Credits", "0.06 Credits", "1.87 Credit"):
            self.assertIn(detail, text)
        self.assertIn("a `name` of 1–100 characters", text)

    def test_shared_auth_distinguishes_oauth_tokens(self) -> None:
        auth = (ROOT / "skills" / "_shared" / "authentication.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("currently 15 days", auth)
        self.assertIn("HTTP 200 from `/oauth2/revoke`", auth)
        self.assertIn("`credentials:*`", skill_text("acedatacloud"))


if __name__ == "__main__":
    unittest.main()
