from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]


def read_skill(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


class RecentDocsSyncTests(unittest.TestCase):
    def test_kling_video_documents_openapi_defaults(self) -> None:
        body = read_skill("kling-video")

        self.assertIn("Quality mode (default `std`;", body)
        self.assertIn("Duration in seconds (default `5`)", body)

    def test_flux_image_documents_required_size(self) -> None:
        body = read_skill("flux-image")

        self.assertIn("`size` is required on `/flux/images`", body)
        self.assertIn('"model": "flux-kontext-pro",\n  "size": "16:9"', body)
