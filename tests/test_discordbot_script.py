from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).parents[1] / "skills" / "discordbot" / "scripts" / "discordbot.py"
SPEC = importlib.util.spec_from_file_location("discordbot_skill", SCRIPT)
assert SPEC and SPEC.loader
discordbot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(discordbot)

RECIPIENT_ID = "123456789012345678"
CHANNEL_ID = "223456789012345678"
CONSENT_MESSAGE_ID = "323456789012345678"
BOT_ID = "423456789012345678"
DM_CHANNEL_ID = "523456789012345678"
SENT_MESSAGE_ID = "623456789012345678"


class DiscordBotScriptTests(unittest.TestCase):
    def call_send(self):
        return discordbot.send_opt_in_dm(
            recipient_id=RECIPIENT_ID,
            consent_channel_id=CHANNEL_ID,
            consent_message_id=CONSENT_MESSAGE_ID,
            consent_keyword="details",
            content="Here are the details.",
        )

    @patch.object(discordbot, "api_request")
    def test_send_verifies_consent_and_posts_one_dm(self, api_request) -> None:
        api_request.side_effect = [
            {"id": BOT_ID, "bot": True},
            {
                "id": CONSENT_MESSAGE_ID,
                "author": {"id": RECIPIENT_ID, "bot": False},
                "content": "  DETAILS  ",
            },
            {"id": DM_CHANNEL_ID},
            [],
            {"id": SENT_MESSAGE_ID},
        ]

        result = self.call_send()

        self.assertEqual(result["status"], "sent")
        self.assertEqual(result["message_id"], SENT_MESSAGE_ID)
        self.assertEqual(
            api_request.call_args_list,
            [
                unittest.mock.call("GET", "/users/@me"),
                unittest.mock.call("GET", f"/channels/{CHANNEL_ID}/messages/{CONSENT_MESSAGE_ID}"),
                unittest.mock.call("POST", "/users/@me/channels", {"recipient_id": RECIPIENT_ID}),
                unittest.mock.call("GET", f"/channels/{DM_CHANNEL_ID}/messages?limit=100"),
                unittest.mock.call("POST", f"/channels/{DM_CHANNEL_ID}/messages", {"content": "Here are the details."}),
            ],
        )

    @patch.object(discordbot, "api_request")
    def test_rejects_consent_from_another_user_before_opening_dm(self, api_request) -> None:
        api_request.side_effect = [
            {"id": BOT_ID, "bot": True},
            {
                "id": CONSENT_MESSAGE_ID,
                "author": {"id": "723456789012345678", "bot": False},
                "content": "details",
            },
        ]

        with self.assertRaisesRegex(discordbot.DiscordBotError, "author does not match"):
            self.call_send()
        self.assertEqual(api_request.call_count, 2)

    @patch.object(discordbot, "api_request")
    def test_rejects_non_exact_consent_keyword_before_opening_dm(self, api_request) -> None:
        api_request.side_effect = [
            {"id": BOT_ID, "bot": True},
            {
                "id": CONSENT_MESSAGE_ID,
                "author": {"id": RECIPIENT_ID, "bot": False},
                "content": "tell me details maybe",
            },
        ]

        with self.assertRaisesRegex(discordbot.DiscordBotError, "exactly match"):
            self.call_send()
        self.assertEqual(api_request.call_count, 2)

    @patch.object(discordbot, "api_request")
    def test_identical_prior_dm_is_not_sent_again(self, api_request) -> None:
        api_request.side_effect = [
            {"id": BOT_ID, "bot": True},
            {
                "id": CONSENT_MESSAGE_ID,
                "author": {"id": RECIPIENT_ID, "bot": False},
                "content": "details",
            },
            {"id": DM_CHANNEL_ID},
            [
                {
                    "id": SENT_MESSAGE_ID,
                    "author": {"id": BOT_ID, "bot": True},
                    "content": "Here are the details.",
                }
            ],
        ]

        result = self.call_send()

        self.assertEqual(result["status"], "duplicate_skipped")
        self.assertEqual(api_request.call_count, 4)

    @patch.object(discordbot, "api_request")
    def test_invalid_recipient_is_rejected_without_network(self, api_request) -> None:
        with self.assertRaisesRegex(discordbot.DiscordBotError, "recipient_id"):
            discordbot.send_opt_in_dm(
                recipient_id="not-a-user",
                consent_channel_id=CHANNEL_ID,
                consent_message_id=CONSENT_MESSAGE_ID,
                consent_keyword="details",
                content="Here are the details.",
            )
        api_request.assert_not_called()

    @patch.object(discordbot, "api_request")
    def test_bot_authored_consent_is_rejected(self, api_request) -> None:
        api_request.side_effect = [
            {"id": BOT_ID, "bot": True},
            {
                "id": CONSENT_MESSAGE_ID,
                "author": {"id": RECIPIENT_ID, "bot": True},
                "content": "details",
            },
        ]

        with self.assertRaisesRegex(discordbot.DiscordBotError, "bot-authored"):
            self.call_send()
        self.assertEqual(api_request.call_count, 2)

    def test_content_equal_to_confirm_flag_is_not_confirmation(self) -> None:
        args, confirm_mode = discordbot.parse_cli(
            [
                "send-opt-in-dm",
                "--recipient-id",
                RECIPIENT_ID,
                "--consent-channel-id",
                CHANNEL_ID,
                "--consent-message-id",
                CONSENT_MESSAGE_ID,
                "--consent-keyword",
                "details",
                "--content=--confirm",
            ]
        )

        self.assertEqual(args.content, "--confirm")
        self.assertEqual(confirm_mode, "")

    def test_confirmation_flag_must_be_final(self) -> None:
        with self.assertRaises(SystemExit):
            discordbot.parse_cli(
                [
                    "send-opt-in-dm",
                    "--confirm",
                    "--recipient-id",
                    RECIPIENT_ID,
                    "--consent-channel-id",
                    CHANNEL_ID,
                    "--consent-message-id",
                    CONSENT_MESSAGE_ID,
                    "--consent-keyword",
                    "details",
                    "--content",
                    "Approved content",
                ]
            )


if __name__ == "__main__":
    unittest.main()
