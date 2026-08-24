from pathlib import Path
import unittest


SKILL = Path(__file__).parents[1] / "skills" / "ai-chat" / "SKILL.md"


class AIChatSkillTests(unittest.TestCase):
    def test_glm_examples_include_latest_docs_model(self) -> None:
        body = SKILL.read_text(encoding="utf-8")
        self.assertIn("`glm-5.3`", body)


if __name__ == "__main__":
    unittest.main()
