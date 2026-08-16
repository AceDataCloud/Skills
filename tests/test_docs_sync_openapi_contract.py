import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SUNO_SKILL = ROOT / "skills" / "suno-music" / "SKILL.md"
SEEDANCE_SKILL = ROOT / "skills" / "seedance-video" / "SKILL.md"


class DocsSyncOpenAPIContractTests(unittest.TestCase):
    def test_suno_vox_documents_required_time_window_fields(self) -> None:
        text = SUNO_SKILL.read_text(encoding="utf-8")
        self.assertIn("requires `audio_id`, `vocal_start` (>=0), `vocal_end` (>0)", text)

    def test_seedance_documents_2x_reference_audio_video_support(self) -> None:
        text = SEEDANCE_SKILL.read_text(encoding="utf-8")
        self.assertIn("supported in **Seedance 2.x** (including 2.5)", text)

    def test_seedance_documents_model_dependent_duration_limits(self) -> None:
        text = SEEDANCE_SKILL.read_text(encoding="utf-8")
        self.assertIn("**2.5 supports up to 30**", text)
        self.assertIn("`-1` is used for 2.5 edit mode", text)


if __name__ == "__main__":
    unittest.main()
