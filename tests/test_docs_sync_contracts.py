import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def skill(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text()


class DocsSyncContractTests(unittest.TestCase):
    def test_ai_chat_lists_current_gemini_models(self) -> None:
        text = skill("ai-chat")
        self.assertIn("`gemini-3.7-flash`", text)
        self.assertIn("`gemini-3.1-flash-lite`", text)
        self.assertNotIn("`gemini-3.1-pro`", text)
        self.assertNotIn("`gemini-2.0-flash-lite`", text)

    def test_fish_documents_final_cost_response(self) -> None:
        text = skill("fish-audio")
        self.assertIn('"cost":{"amount":1,"currency":"Credits","list_amount":1}', text)
        self.assertIn("terminal `/fish/tasks` response includes it in `response.cost`", text)

    def test_maestro_documents_unified_limits_and_pricing(self) -> None:
        text = skill("maestro-video")
        self.assertIn("maximum 20", text)
        self.assertIn("maximum 4", text)
        self.assertIn("0.60 Credits per actual delivered second", text)
        self.assertNotIn("### Production SKUs", text)
        self.assertNotIn("| `quality` |", text)
