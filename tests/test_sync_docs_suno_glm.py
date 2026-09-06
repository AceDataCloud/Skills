import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SUNO_SKILL = ROOT / "skills" / "suno-music" / "SKILL.md"
AI_CHAT_SKILL = ROOT / "skills" / "ai-chat" / "SKILL.md"


class SunoSkillSyncTests(unittest.TestCase):
    def test_suno_skill_mentions_mp3_conversion_endpoint(self) -> None:
        text = SUNO_SKILL.read_text()
        self.assertIn("`/suno/mp3`", text)

    def test_suno_skill_no_longer_documents_custom_models_endpoint(self) -> None:
        text = SUNO_SKILL.read_text()
        self.assertNotIn("/suno/custom-models", text)


class AiChatGlmSyncTests(unittest.TestCase):
    def test_glm_examples_match_current_openapi_family(self) -> None:
        text = AI_CHAT_SKILL.read_text()
        self.assertIn("`glm-5.3`", text)
        self.assertNotIn("`glm-4.5`", text)
        self.assertNotIn("`glm-4.5v`", text)


if __name__ == "__main__":
    unittest.main()
