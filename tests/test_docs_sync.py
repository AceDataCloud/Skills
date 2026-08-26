from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]


def read_skill(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


class DocsSyncTests(unittest.TestCase):
    def test_turnstile_documents_server_managed_captcha_tasks(self) -> None:
        body = read_skill("turnstile")
        self.assertIn("/captcha/tasks", body)
        self.assertIn("never advances task processing", body)
        self.assertIn("120-second deadline", body)
        self.assertIn("reading `processing`, and timed-out tasks are not charged", body)

    def test_gpt_image_2_documents_current_openapi_variants_and_inputs(self) -> None:
        body = read_skill("gpt-image-2")
        self.assertIn("gpt-image-2:official", body)
        self.assertIn("gpt-image-2:reverse", body)
        self.assertIn("JSON `image` URLs/base64 strings", body)
        self.assertIn("up to 16", body)
        self.assertIn("`output_format` supports `png`, `jpeg`, or `webp`", body)

    def test_qwen_and_wan_document_current_controls(self) -> None:
        qwen = read_skill("qwen-image")
        self.assertIn("`prompt_extend_mode` is `direct` or `agent`", qwen)
        self.assertIn("`seed` (0–2147483647)", qwen)

        wan = read_skill("wan-video")
        self.assertIn("`wan3.0-video`", wan)
        self.assertIn("`ratio`", wan)
        self.assertIn("`watermark`", wan)
        self.assertIn("Wan 3 supports 2–30 seconds or `-1` automatic duration", wan)
