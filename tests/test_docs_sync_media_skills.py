import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def skill_body(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text()


class DocsSyncMediaSkillTests(unittest.TestCase):
    def test_gpt_image_2_documents_current_edit_size_auto_behavior(self) -> None:
        text = skill_body("gpt-image-2")
        self.assertIn("`gpt-image-2:official`", text)
        self.assertIn("array of up to 16 images", text)
        self.assertIn('omitting\n`size` is equivalent to `"auto"`', text)
        self.assertIn("falls back to the first reference image size", text)
        self.assertIn("not retried automatically", text)

    def test_qwen_image_documents_current_optional_controls(self) -> None:
        text = skill_body("qwen-image")
        self.assertIn("`prompt_extend_mode` defaults to `direct`", text)
        self.assertIn("`negative_prompt`", text)
        self.assertIn("`seed` (0–2147483647)", text)

    def test_wan_video_documents_current_wan3_parameters(self) -> None:
        text = skill_body("wan-video")
        self.assertIn("`wan3.0-video`", text)
        self.assertIn('`ratio` | No | `"adaptive"`, `"16:9"', text)
        self.assertIn("`duration` | No | `2`–`30` or `-1`", text)
        self.assertIn("`seed` | No | integer 0–2147483647", text)

    def test_kling_motion_documents_model_name(self) -> None:
        text = skill_body("kling-video")
        self.assertIn('`model_name` (`/kling/motion`) | `"kling-v2-6"`, `"kling-v3"`', text)


if __name__ == "__main__":
    unittest.main()
