#!/usr/bin/env python3
"""Permission-first Discord Bot actions."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

API_BASE = "https://discord.com/api/v10"
SNOWFLAKE_RE = re.compile(r"[0-9]{17,20}")


class DiscordBotError(RuntimeError):
    pass


def out(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def normalize_text(value: str) -> str:
    return " ".join(value.split()).casefold()


def validate_snowflake(name: str, value: str) -> str:
    value = value.strip()
    if not SNOWFLAKE_RE.fullmatch(value):
        raise DiscordBotError(f"{name} must be a 17-20 digit Discord snowflake")
    return value


def validate_send_input(
    recipient_id: str,
    consent_channel_id: str,
    consent_message_id: str,
    consent_keyword: str,
    content: str,
) -> dict[str, str]:
    values = {
        "recipient_id": validate_snowflake("recipient_id", recipient_id),
        "consent_channel_id": validate_snowflake("consent_channel_id", consent_channel_id),
        "consent_message_id": validate_snowflake("consent_message_id", consent_message_id),
        "consent_keyword": consent_keyword.strip(),
        "content": content.strip(),
    }
    if not values["consent_keyword"] or len(values["consent_keyword"]) > 64:
        raise DiscordBotError("consent_keyword must contain 1-64 characters")
    if not values["content"] or len(values["content"]) > 2000:
        raise DiscordBotError("content must contain 1-2000 characters")
    return values


def api_request(method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
    token = os.environ.get("DISCORDBOT_TOKEN", "").strip()
    if not token:
        raise DiscordBotError(
            "DISCORDBOT_TOKEN is not set; connect Discord Bot at "
            "https://auth.acedata.cloud/user/connections"
        )
    body = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        f"{API_BASE}{path}",
        data=body,
        method=method,
        headers={
            "Authorization": f"Bot {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "AceDataCloud-DiscordBot/1.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            detail = json.loads(raw.decode())
            message = str(detail.get("message") or detail.get("code") or "request rejected")
            retry_after = detail.get("retry_after")
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            message = "request rejected"
            retry_after = None
        suffix = f"; retry_after={retry_after}" if retry_after is not None else ""
        raise DiscordBotError(f"Discord API {exc.code}: {message}{suffix}") from None
    except urllib.error.URLError as exc:
        raise DiscordBotError(f"Discord API unavailable: {exc.reason}") from None

    if not raw:
        return None
    try:
        return json.loads(raw.decode())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DiscordBotError("Discord API returned invalid JSON") from exc


def send_opt_in_dm(
    recipient_id: str,
    consent_channel_id: str,
    consent_message_id: str,
    consent_keyword: str,
    content: str,
) -> dict[str, Any]:
    values = validate_send_input(
        recipient_id,
        consent_channel_id,
        consent_message_id,
        consent_keyword,
        content,
    )
    recipient_id = values["recipient_id"]
    consent_channel_id = values["consent_channel_id"]
    consent_message_id = values["consent_message_id"]
    consent_keyword = values["consent_keyword"]
    content = values["content"]

    bot = api_request("GET", "/users/@me")
    bot_id = validate_snowflake("bot id", str(bot.get("id", "")))
    if not bot.get("bot"):
        raise DiscordBotError("connected credential is not a Discord bot token")

    source = api_request("GET", f"/channels/{consent_channel_id}/messages/{consent_message_id}")
    if str(source.get("id", "")) != consent_message_id:
        raise DiscordBotError("Discord returned a different consent message")
    author = source.get("author") or {}
    if str(author.get("id", "")) != recipient_id:
        raise DiscordBotError("consent message author does not match recipient_id")
    if author.get("bot"):
        raise DiscordBotError("bot-authored messages cannot grant DM consent")
    if normalize_text(str(source.get("content", ""))) != normalize_text(consent_keyword):
        raise DiscordBotError("consent message does not exactly match consent_keyword")

    dm = api_request("POST", "/users/@me/channels", {"recipient_id": recipient_id})
    dm_channel_id = validate_snowflake("DM channel id", str(dm.get("id", "")))

    history = api_request("GET", f"/channels/{dm_channel_id}/messages?limit=100")
    if not isinstance(history, list):
        raise DiscordBotError("Discord returned invalid DM history")
    duplicate = next(
        (
            message
            for message in history
            if str((message.get("author") or {}).get("id", "")) == bot_id
            and str(message.get("content", "")) == content
        ),
        None,
    )
    if duplicate:
        return {
            "status": "duplicate_skipped",
            "recipient_id": recipient_id,
            "consent_message_id": consent_message_id,
            "dm_channel_id": dm_channel_id,
            "message_id": duplicate.get("id"),
        }

    sent = api_request("POST", f"/channels/{dm_channel_id}/messages", {"content": content})
    return {
        "status": "sent",
        "recipient_id": recipient_id,
        "consent_message_id": consent_message_id,
        "dm_channel_id": dm_channel_id,
        "message_id": sent.get("id"),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    send = commands.add_parser("send-opt-in-dm", help="send one DM after verifying an exact opt-in message")
    send.add_argument("--recipient-id", required=True)
    send.add_argument("--consent-channel-id", required=True)
    send.add_argument("--consent-message-id", required=True)
    send.add_argument("--consent-keyword", required=True)
    send.add_argument("--content", required=True)
    send.add_argument("--confirm", action="store_true", help=argparse.SUPPRESS)
    send.add_argument("--unattended-confirm", action="store_true", help=argparse.SUPPRESS)
    return parser


def parse_cli(raw: list[str] | None = None) -> tuple[argparse.Namespace, str]:
    raw = list(sys.argv[1:] if raw is None else raw)
    parser = build_parser()
    args = parser.parse_args(raw)
    if args.confirm and args.unattended_confirm:
        parser.error("choose only one confirmation mode")
    confirm_mode = "--confirm" if args.confirm else "--unattended-confirm" if args.unattended_confirm else ""
    if confirm_mode and (not raw or raw[-1] != confirm_mode):
        parser.error(f"{confirm_mode} must be the final argument")
    return args, confirm_mode


def main() -> None:
    args, confirm_mode = parse_cli()
    try:
        values = validate_send_input(
            args.recipient_id,
            args.consent_channel_id,
            args.consent_message_id,
            args.consent_keyword,
            args.content,
        )
        if not confirm_mode:
            out(
                {
                    "status": "dry_run",
                    "recipient_id": values["recipient_id"],
                    "consent_channel_id": values["consent_channel_id"],
                    "consent_message_id": values["consent_message_id"],
                    "consent_keyword": values["consent_keyword"],
                    "content": values["content"],
                    "next": "rerun with trailing --confirm after user approval",
                }
            )
            return
        out(send_opt_in_dm(**values))
    except DiscordBotError as exc:
        out({"error": str(exc)})
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
