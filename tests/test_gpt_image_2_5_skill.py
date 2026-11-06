import json
import re
import shlex
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

    def test_reverse_aliases_preserve_identity_and_request_formats(self) -> None:
        text = SKILL.read_text()
        for variant in ("flare", "sunburst"):
            with self.subTest(variant=variant):
                self.assertIn(
                    f"`gpt-image-2.5-{variant}:reverse` — explicit reverse alias, "
                    f"equivalent to `gpt-image-2.5-{variant}`.", text
                )
        for requirement in (
            "replace `model` in Generate or Edit with the complete `:reverse` alias",
            "preserve the suffix",
            "Both aliases support generation JSON, URL-edit JSON and multipart file edits",
            "same parameter limits as their unsuffixed names",
            '-F "model=gpt-image-2.5-sunburst:reverse"',
            "`n` accepts 1–10", "`b64_json` requires `n=1`",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)

    def test_reverse_billing_and_recovery_do_not_change_requested_model(self) -> None:
        legacy = SKILL.parent.parent / "gpt-image-2" / "SKILL.md"
        for skill in (SKILL, legacy):
            with self.subTest(skill=skill.parent.name):
                text = skill.read_text()
                for requirement in (
                    "bill per successful image", "0.19 Credits per image",
                    "for generation and editing", "final usage records",
                    "token statistics", "do not change", "billing mode",
                    "automatic recovery", "may be fulfilled using GPT Image 2.5 Flare",
                    "requested model and per-successful-image billing remain unchanged",
                    "Do not resubmit to force recovery or silently change the user's requested model",
                ):
                    with self.subTest(requirement=requirement):
                        self.assertIn(requirement, text)
                self.assertNotIn("0.11", text)

    def test_quality_levels_are_model_scoped_and_cover_both_edit_formats(self) -> None:
        text = SKILL.read_text().split("## Shared contract\n", 1)[1]
        quality = next(line for line in text.splitlines() if line.startswith("- For generation and editing, `quality`"))
        for requirement in (
            "`auto` (default), `low`, `medium`, or `high`",
            "GPT Image 2.5 and 2.6 Flare/Sunburst",
            "including their `:reverse` and `:official` variants",
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

    def test_gif_procedure_preserves_models_and_validation_boundaries(self) -> None:
        text = SKILL.read_text().split("## Animated GIF (GPT Image 2.6)\n", 1)[1]
        text = text.split("## Planning complexity", 1)[0]
        for variant in ("flare", "sunburst"):
            for suffix in ("", ":reverse", ":official"):
                self.assertIn(f"`gpt-image-2.6-{variant}{suffix}`", text)
        for requirement in (
            "integers from 2 to 16", "integer from 20 to 655350 ms",
            "nearest 10ms", "Frame controls apply only to GIF",
            'size: "auto"', "different actual dimensions",
            "image-to-GIF", "/openai/images/edits",
            "`n` counts returned GIF files, not animation frames",
            "do not resubmit a pending job", "per-successful-file",
            "official token billing", "model pixel budget",
            "`mask`, `markup`, `output_compression`, `prompt_rewriter`",
            "partial-image streaming", "rejected before generation",
            "not blanket support for every 1K combination or 4K GIF",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        example = json.loads(re.search(r"```json\n(.*?)\n```", text, re.S)[1])
        self.assertEqual(example["model"], "gpt-image-2.6-flare")
        self.assertEqual(example["output_format"], "gif")
        self.assertEqual(example["size"], "512x512")
        self.assertEqual(example["frame_count"], 9)
        self.assertEqual(example["frame_duration_ms"], 200)
        self.assertEqual(example["n"], 1)
        self.assertIs(example["async"], True)

    def test_complexity_and_markup_are_actionable_and_model_scoped(self) -> None:
        text = SKILL.read_text()
        complexity = text.split("## Planning complexity (GPT Image 2.6 only)\n", 1)[1]
        complexity = complexity.split("## Annotation-guided", 1)[0]
        for requirement in (
            'complexity: "low"', '"medium"', '"high"',
            '-F "complexity=medium"', "model default `high`",
            "independently of rendering `quality`", "no separate per-request surcharge",
            "official variants still bill actual token usage", "Do not send it to other models",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, complexity)
        markup = text.split("## Annotation-guided static editing (GPT Image 2.6 only)\n", 1)[1]
        for requirement in (
            "transparent pixels", "first reference image after orientation correction",
            "explain the intended changes in `prompt`", "16,777,216 pixels", "40MB",
            "HTTPS URL, PNG base64 data URL", "object containing only `image_url`",
            "multipart accepts an annotation file or HTTPS URL",
            "`file_id` is not supported", "with `mask`, GIF or `prompt_rewriter`",
            "Omit `input_fidelity`", "Poll the same task ID",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, markup)
        command = re.search(r"```bash\n(.*?)\n```", markup, re.S)[1]
        args = shlex.split(command.replace("\\\n", ""))
        fields = dict(args[i + 1].split("=", 1) for i, arg in enumerate(args) if arg == "-F")
        self.assertIn("https://api.acedata.cloud/openai/images/edits", args)
        self.assertEqual(fields["model"], "gpt-image-2.6-sunburst:reverse")
        self.assertEqual(fields["image"], "@input.png")
        self.assertEqual(fields["markup"], "@annotation.png")
        self.assertEqual(fields["output_format"], "png")
        self.assertEqual(fields["complexity"], "medium")
        self.assertEqual(fields["async"], "true")
        for excluded in ("mask", "input_fidelity", "prompt_rewriter", "file_id"):
            self.assertNotIn(excluded, fields)

    def test_static_4k_requires_concrete_pixels(self) -> None:
        text = SKILL.read_text()
        self.assertIn("Static generation and editing", text)
        self.assertIn('pass concrete pixels, not `size: "4K"`', text)
        self.assertIn("`4096x4096` exceeds the pixel limit", text)
        self.assertIn("SVG is not exposed", text)

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
