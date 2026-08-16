import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AI_CHAT = ROOT / "skills" / "ai-chat" / "SKILL.md"
MINIMAX = ROOT / "skills" / "minimax-video" / "SKILL.md"
SUNO = ROOT / "skills" / "suno-music" / "SKILL.md"


class DocsSyncContractTests(unittest.TestCase):
    def test_ai_chat_documents_responses_controls(self) -> None:
        text = AI_CHAT.read_text(encoding="utf-8")
        self.assertIn("## OpenAI-Compatible Responses", text)
        self.assertIn("`parallel_tool_calls`", text)
        self.assertIn("`include`", text)
        self.assertIn("`max_output_tokens`", text)
        self.assertIn("`store`", text)

    def test_minimax_documents_async_default_and_task_id_response(self) -> None:
        text = MINIMAX.read_text(encoding="utf-8")
        self.assertIn("| `async` | `true`, `false` | `true` |", text)
        self.assertIn("returns `task_id` and `trace_id`", text)

    def test_suno_documents_required_vox_range(self) -> None:
        text = SUNO.read_text(encoding="utf-8")
        self.assertIn(
            "requires `audio_id`, `vocal_start` (≥ 0), and `vocal_end` (> 0)",
            text,
        )

    def test_seedance_gotchas_reflect_25_capabilities(self) -> None:
        text = (ROOT / "skills" / "seedance-video" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("2.5 also supports pure-audio reference", text)
        self.assertIn("2.5 supports 4–30 seconds", text)


if __name__ == "__main__":
    unittest.main()
