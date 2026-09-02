import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class DocsApiSyncTests(unittest.TestCase):
    def test_fish_documents_successful_response_cost(self) -> None:
        text = (ROOT / "skills" / "fish-audio" / "SKILL.md").read_text()
        self.assertIn('"cost": {"amount": 1, "currency": "Credits", "list_amount": 1}', text)
        self.assertIn("terminal `response.cost` matches the callback's top-level `cost`", text)

    def test_maestro_documents_current_limits_without_tiers(self) -> None:
        text = (ROOT / "skills" / "maestro-video" / "SKILL.md").read_text()
        self.assertIn("Public image, video, or audio references (up to 20)", text)
        self.assertNotIn("drama`: acted short drama with characters and dialogue (Pro only)", text)

    def test_seedance_documents_reference_task_type(self) -> None:
        text = (ROOT / "skills" / "seedance-video" / "SKILL.md").read_text()
        self.assertIn('`omni_reference_task_type: "auto"`, `"reference"`, `"edit"`, or `"extend"`', text)
        self.assertIn("`reference` requires at least one `reference_image`, `reference_video`, or `reference_audio`", text)


if __name__ == "__main__":
    unittest.main()
