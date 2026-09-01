from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]


class DocsSyncTests(unittest.TestCase):
    def test_fish_skill_documents_successful_response_cost(self) -> None:
        content = (ROOT / "skills" / "fish-audio" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('"cost": {"amount": 1, "currency": "Credits", "list_amount": 1}', content)
        self.assertIn("results include it as `response.cost`", content)

    def test_ai_chat_skill_lists_current_gemini_models(self) -> None:
        content = (ROOT / "skills" / "ai-chat" / "SKILL.md").read_text(encoding="utf-8")
        for model in (
            "gemini-3.7-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.1-pro-preview",
            "gemini-2.5-pro",
        ):
            self.assertIn(f"`{model}`", content)
        for removed_model in (
            "gemini-3.1-pro`",
            "gemini-3.1-flash-lite-preview",
            "gemini-3-pro-preview",
            "gemini-2.0-flash-lite",
        ):
            self.assertNotIn(removed_model, content)
