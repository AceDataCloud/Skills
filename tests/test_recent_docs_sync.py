from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]


def read_skill(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


class RecentDocsSyncTests(unittest.TestCase):
    def test_flux_documents_required_size(self) -> None:
        body = read_skill("flux-image")
        edit_section = body.split("## Edit Images", 1)[1].split("## Gotchas", 1)[0]

        self.assertIn('"size": "1:1"', edit_section)
        self.assertIn("`size` is required for both generation and editing requests", body)

    def test_kling_documents_video_defaults(self) -> None:
        body = read_skill("kling-video")

        self.assertIn('defaults to `"std"`', body)
        self.assertIn("defaults to `5`", body)


if __name__ == "__main__":
    unittest.main()
