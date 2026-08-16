from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
AI_CHAT = ROOT / "skills" / "ai-chat" / "SKILL.md"
SUNO = ROOT / "skills" / "suno-music" / "SKILL.md"


class OpenAPISyncDocsTests(unittest.TestCase):
    def test_ai_chat_documents_openai_models_metadata_and_responses_fields(self) -> None:
        body = AI_CHAT.read_text(encoding="utf-8")

        self.assertIn("GET /openai/models", body)
        self.assertIn("models[]", body)
        self.assertIn("supported reasoning levels", body)
        self.assertIn("input_modalities", body)
        self.assertIn("parallel-tool-call support", body)

        self.assertIn("POST /openai/responses", body)
        for field in (
            "parallel_tool_calls",
            "tool_choice",
            "reasoning",
            "max_output_tokens",
            "stream_options",
            "additional_tools",
            "custom_tool_call_output",
        ):
            self.assertIn(field, body)

    def test_suno_documents_required_vox_time_range(self) -> None:
        body = SUNO.read_text(encoding="utf-8")

        self.assertIn("`/suno/vox` | POST | Extract vocal track", body)
        self.assertIn("requires `audio_id`, `vocal_start` (>= 0), and `vocal_end` (> 0)", body)
        self.assertIn("send `vocal_start` (0 or greater) and `vocal_end` (greater than 0)", body)


if __name__ == "__main__":
    unittest.main()
