from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]


def skill(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text()


class DocsSyncTests(unittest.TestCase):
    def test_ai_chat_lists_deepseek_v4_pro(self) -> None:
        self.assertIn("`deepseek-v4-pro`", skill("ai-chat"))

    def test_flux_documents_required_size_for_edits(self) -> None:
        flux = skill("flux-image")
        edit_section = flux.split("## Edit Images", 1)[1].split("## Gotchas", 1)[0]
        self.assertIn('"size": "16:9"', edit_section)
        self.assertIn("`size` is required", flux)


if __name__ == "__main__":
    unittest.main()
