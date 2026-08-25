from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class DocsSyncTests(unittest.TestCase):
    def test_ai_chat_lists_current_glm_model(self) -> None:
        body = text("skills/ai-chat/SKILL.md")
        self.assertIn("`glm-5.3`", body)

    def test_gpt_image_2_documents_auto_edit_size_semantics(self) -> None:
        body = text("skills/gpt-image-2/SKILL.md")
        self.assertIn('Omitting `size` is equivalent to `"auto"`', body)
        self.assertIn("falls back to the first reference", body)
        self.assertIn("normalized before submission", body)


if __name__ == "__main__":
    unittest.main()
