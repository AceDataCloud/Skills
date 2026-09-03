import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class DocsSync1058Tests(unittest.TestCase):
    def test_seedance_includes_reference_task_type(self) -> None:
        text = (ROOT / "skills" / "seedance-video" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`auto`, `reference`, `edit`, `extend`", text)

    def test_fish_documents_cost_in_sync_response(self) -> None:
        text = (ROOT / "skills" / "fish-audio" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('"cost":{"amount":0.0123,"currency":"credit","list_amount":0.0134}', text)
        self.assertIn("`cost.amount` is the actual deducted Credits", text)

    def test_maestro_file_urls_limit(self) -> None:
        text = (ROOT / "skills" / "maestro-video" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("up to 20 URLs", text)


if __name__ == "__main__":
    unittest.main()
