import unittest
from pathlib import Path


SKILL = Path(__file__).parents[1] / "skills" / "gpt-image-2-5" / "SKILL.md"


class GPTImage25SkillContractTests(unittest.TestCase):
    def test_official_variants_are_documented(self) -> None:
        text = SKILL.read_text()

        self.assertIn("gpt-image-2.5-flare:official", text)
        self.assertIn("gpt-image-2.5-sunburst:official", text)
        self.assertIn("actual text, reference-image, and output-image tokens", text)
        self.assertIn("Do not send `gpt-image-2.5` or `gpt-image-2.5:reverse`", text)

    def test_quality_levels_are_model_scoped_and_cover_both_edit_formats(self) -> None:
        text = SKILL.read_text().split("## Shared contract\n", 1)[1]
        quality = next(line for line in text.splitlines() if line.startswith("- For generation and editing, `quality`"))
        for requirement in (
            "`auto` (default), `low`, `medium`, or `high`",
            "Only `gpt-image-2.5-flare` and `gpt-image-2.5-sunburst`",
            "including their `:official` variants",
            "`xhigh` and `max`",
            "do not use those extra levels with other GPT Image models",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, quality)
        for requirement in (
            "generation JSON, URL-edit JSON, or multipart file edits",
            '"quality":"xhigh"', '-F "quality=max"',
            "quality affects token usage",
            "pre-request price is an estimate, not the final charge",
            "use returned usage records for final cost",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)

    def test_regional_catalog_check_preserves_access_and_unrelated_media(self) -> None:
        text = SKILL.read_text().split("## Regional catalog check\n", 1)[1]
        text = text.split("## Generate\n", 1)[0]
        for requirement in (
            "`image_unavailable_regions`", "`unavailable_regions`",
            "Mainland-China catalog views hide OpenAI image generation/editing and companion guides",
            "Raw REST results may still contain marked rows",
            "requesting visitor's IP", "not the display language or a `?country=` override",
            "Do not recommend region-hidden images from a cached global catalog",
            "or hide unrelated OpenAI capabilities",
            "does not change API routing or billing",
            "not proof of retirement or revoked API access",
            "check actual account access, key restrictions and pricing",
            "do not silently substitute another model",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertNotIn("```", text)


if __name__ == "__main__":
    unittest.main()
