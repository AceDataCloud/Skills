from pathlib import Path
import unittest


SKILL = Path(__file__).parents[1] / "skills" / "discordbot" / "SKILL.md"


class DiscordBotSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.content = SKILL.read_text(encoding="utf-8")

    def test_skill_has_one_frontmatter_block(self) -> None:
        self.assertTrue(self.content.startswith("---\n"))
        self.assertEqual(self.content.count("\n---\n"), 1)
        self.assertIn('version: "1.1"', self.content)

    def test_read_recipe_returns_opt_in_evidence_fields(self) -> None:
        self.assertIn("author_id: .author.id", self.content)
        self.assertIn("id, author_id:", self.content)

    def test_dm_recipe_uses_official_single_recipient_endpoint(self) -> None:
        self.assertIn('python3 "$SKILL_DIR/scripts/discordbot.py" send-opt-in-dm', self.content)
        self.assertIn('--recipient-id "$RECIPIENT_ID"', self.content)
        self.assertIn('--consent-message-id "$CONSENT_MESSAGE_ID"', self.content)
        self.assertIn("Send to exactly one recipient per invocation", self.content)

    def test_unattended_dm_requires_preapproved_evidence(self) -> None:
        self.assertIn("one exact `recipient_id`", self.content)
        self.assertIn("`consent_channel_id`", self.content)
        self.assertIn("`consent_message_id`", self.content)
        self.assertIn("`consent_keyword`", self.content)
        self.assertIn("approved `content`", self.content)
        self.assertIn("return a draft without sending", self.content)

    def test_bulk_and_nonconsensual_dm_are_forbidden(self) -> None:
        self.assertIn("Server membership, a public", self.content)
        self.assertIn("profile, or appearing in a member list is not consent", self.content)
        self.assertIn("Never enumerate members", self.content)
        self.assertIn("Do not call the", self.content)
        self.assertIn("Create DM endpoint directly", self.content)


if __name__ == "__main__":
    unittest.main()