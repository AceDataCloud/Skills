from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]


def read_skill(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


class DocsSyncOpenAPITests(unittest.TestCase):
    def test_ai_chat_lists_latest_glm_model(self) -> None:
        self.assertIn("`glm-5.3`", read_skill("ai-chat"))

    def test_qwen_image_documents_cost_response(self) -> None:
        text = read_skill("qwen-image")
        self.assertIn("`cost`", text)
        self.assertIn("`amount`", text)
        self.assertIn("`currency`", text)
        self.assertIn("`list_amount`", text)


if __name__ == "__main__":
    unittest.main()
