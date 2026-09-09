"""Regression tests for safe Skill onboarding and async examples."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ACTION4_SKILLS = {
    "flux-image": ("flux_list_models", "POST https://api.acedata.cloud/flux/images"),
    "kling-video": ("kling_list_models", "POST https://api.acedata.cloud/kling/videos"),
    "nano-banana-image": (
        "nanobanana_list_models",
        "POST https://api.acedata.cloud/nano-banana/images",
    ),
    "seedance-video": (
        "seedance_list_models",
        "POST https://api.acedata.cloud/seedance/videos",
    ),
    "seedream-image": (
        "seedream_list_models",
        "curl https://api.acedata.cloud/seedream/images",
    ),
}


class SafeOnboardingTests(unittest.TestCase):
    def skill_text(self, slug: str) -> str:
        return (ROOT / "skills" / slug / "SKILL.md").read_text()

    def test_action4_skills_name_verified_no_charge_tools(self) -> None:
        for slug, (tool, _) in ACTION4_SKILLS.items():
            with self.subTest(skill=slug):
                text = self.skill_text(slug)
                self.assertIn(tool, text)
                self.assertIn("does not call the generation API", text)
                self.assertIn("does not consume credits", text)
                self.assertIn("Do not invoke generation merely to verify setup", text)

    def test_action4_skills_stop_for_confirmation_before_generation(self) -> None:
        for slug, (_, first_paid_request) in ACTION4_SKILLS.items():
            with self.subTest(skill=slug):
                text = self.skill_text(slug)
                confirmation = text.index("Obtain explicit user confirmation")
                paid_request = text.index(first_paid_request)
                self.assertIn("live pricing", text[:paid_request])
                self.assertIn("selected model and options", text[:paid_request])
                self.assertLess(confirmation, paid_request)
                self.assertIn("Stop here until the user confirms", text[:paid_request])

    def test_public_skill_sources_never_use_health_as_callback(self) -> None:
        sources = [*ROOT.glob("skills/**/*.md"), *ROOT.glob("template/**/*.md")]
        pattern = re.compile(
            r'["\'`]callback_url["\'`]?\s*[:=][^\n]*api\.acedata\.cloud/health',
            re.IGNORECASE,
        )
        for path in sources:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsNone(pattern.search(path.read_text()))

    def test_shared_async_guide_requires_a_real_webhook(self) -> None:
        text = (ROOT / "skills" / "_shared" / "async-tasks.md").read_text()
        lowered = text.lower()
        self.assertIn("real public http(s) webhook", lowered)
        self.assertIn("user owns", lowered)
        self.assertIn("never use a health endpoint as a fake callback", lowered)
        self.assertIn("callbacks and polling are independent", lowered)
        self.assertNotIn("always use `callback_url`", lowered)
        self.assertNotIn('always set `"callback_url"`', lowered)


if __name__ == "__main__":
    unittest.main()
