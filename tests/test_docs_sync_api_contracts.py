from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]


class DocsSyncApiContractsTests(unittest.TestCase):
    def test_ai_chat_documents_responses_input_and_tool_contracts(self) -> None:
        text = (ROOT / "skills" / "ai-chat" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("`POST /openai/responses` requires `model` and `input`", text)
        self.assertIn('"type": "custom_tool_call"', text)
        self.assertIn('"type": "custom_tool_call_output"', text)
        self.assertIn("`max_output_tokens`", text)
        self.assertIn("`parallel_tool_calls`", text)
        self.assertIn("`output_text`", text)
        self.assertIn("`response.completed`", text)

    def test_suno_documents_required_vox_boundaries(self) -> None:
        text = (ROOT / "skills" / "suno-music" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("requires `audio_id`, `vocal_start` (≥ 0), and `vocal_end` (> 0)", text)
        self.assertIn("| `lyric_prompt` | string |", text)
