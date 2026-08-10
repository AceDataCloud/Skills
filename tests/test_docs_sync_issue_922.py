import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def skill_text(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


class DocsSyncIssue922Tests(unittest.TestCase):
    def test_face_transform_matches_face_change_response_shapes(self) -> None:
        text = skill_text("face-transform")
        self.assertIn("`face_shape_set` as an array", text)
        self.assertIn("numeric `score`", text)

    def test_producer_documents_nullable_video_url(self) -> None:
        text = skill_text("producer-music")
        self.assertIn('"video_url": null', text)
        self.assertIn("`video_url` in `/producer/audios` responses is nullable", text)

    def test_happyhorse_documents_nullable_output_ratio(self) -> None:
        self.assertIn("Output `ratio` may be `null`", skill_text("happyhorse-video"))

    def test_grok_models_match_current_openapi_surface(self) -> None:
        self.assertNotIn("grok-imagine-video-1.5-preview", skill_text("grok-video"))

    def test_removed_sora_openapi_surface_is_not_advertised(self) -> None:
        self.assertFalse((ROOT / "skills" / "sora-video" / "SKILL.md").exists())
        self.assertNotIn("sora-video", (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertNotIn("mcp-sora", (ROOT / "skills" / "_shared" / "mcp-servers.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
