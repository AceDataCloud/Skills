import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def skill(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


class OpenAPISyncDocTests(unittest.TestCase):
    def test_seedream_documents_latest_generation_options(self) -> None:
        text = skill("seedream-image")
        self.assertIn("doubao-seedream-5-0-lite-260128", text)
        self.assertIn("`layer_decomposition`", text)
        self.assertIn('`background` | `"transparent"`, `"opaque"`', text)
        self.assertIn('"WIDTHxHEIGHT"', text)
        self.assertIn("Accept: application/x-ndjson", text)
        self.assertNotIn('"adaptive"', text)

    def test_suno_upload_documents_enhanced_mode(self) -> None:
        text = skill("suno-music")
        self.assertIn("| `/suno/mp3` | POST |", text)
        self.assertIn('| `mode` | `"standard"`, `"enhanced"` |', text)
        self.assertIn("enhanced upload returns `task_id`/`trace_id`", text)

    def test_ai_chat_model_examples_include_latest_spec_entries(self) -> None:
        text = skill("ai-chat")
        self.assertIn("claude-fable-5-1", text)
        self.assertIn("gemini-3.7-flash", text)
        self.assertIn("glm-5.3", text)


if __name__ == "__main__":
    unittest.main()
