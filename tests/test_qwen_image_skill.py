from __future__ import annotations

import pathlib
import unittest


SKILL = pathlib.Path(__file__).parents[1] / "skills" / "qwen-image" / "SKILL.md"


class QwenImageSkillTests(unittest.TestCase):
    def test_documents_qwen_image_endpoints_and_models(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertTrue(text.startswith("---\n"))
        self.assertEqual(text.count("\n---\n"), 1)
        for value in (
            "POST /qwen-image/images",
            "POST /qwen-image/tasks",
            "qwen-image-3.0",
            "qwen-image-3.0-pro",
            '"action": "retrieve"',
            '"action": "retrieve_batch"',
        ):
            with self.subTest(value=value):
                self.assertIn(value, text)
