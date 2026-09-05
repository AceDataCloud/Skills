from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).parents[1]


def read_skill(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


class DocsSyncTests(unittest.TestCase):
    def test_ai_chat_lists_gpt_6_astra(self) -> None:
        self.assertIn("`gpt-6-astra`", read_skill("ai-chat"))

    def test_fish_tts_reference_id_matches_current_schema(self) -> None:
        text = read_skill("fish-audio")
        self.assertIn("| `reference_id` | string or string[] |", text)
        self.assertIn("mutually exclusive with `references`", text)

    def test_seedream_mentions_prompt_optimization_parameter(self) -> None:
        self.assertIn("`optimize_prompt_options.mode`", read_skill("seedream-image"))


if __name__ == "__main__":
    unittest.main()
