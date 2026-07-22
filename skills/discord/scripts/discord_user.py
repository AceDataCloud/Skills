#!/usr/bin/env python3
"""
discord_user.py — act on Discord with the user's own account (BYOC user-token path).

This is the **BYOC** half of the `discord` skill. It runs only when the user
connected Discord with a personal user token (env ``DISCORD_USER_TOKEN``); the
OAuth half of the skill uses plain ``curl`` and is documented in SKILL.md.

Drives Discord's user API through `discord.py-self`
(https://github.com/dolfies/discord.py-self). This acts as the user's REAL
account, so every state-changing command (send / reply) is GATED by a trailing
``--confirm`` — without it, the command dry-runs.

The connector injects the token as env var ``DISCORD_USER_TOKEN``. It is full
account access — NEVER echo or print it.

Examples:
  python3 discord_user.py whoami
  python3 discord_user.py guilds
  python3 discord_user.py channels --guild 1133012399448928276
  python3 discord_user.py messages --channel 1133012400174534792 --limit 20
  python3 discord_user.py send --channel 1133012400174534792 --text "hello" --confirm
  python3 discord_user.py reply --channel 1133012400174534792 --message 987654321 --text "on it" --confirm
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

_RAW = sys.argv[1:]
# --confirm is honored ONLY as the last token, and only one is stripped, so a
# message body that merely contains "--confirm" can never silently confirm a write.
CONFIRM = bool(_RAW) and _RAW[-1] == "--confirm"
ARGV = _RAW[:-1] if CONFIRM else list(_RAW)

# State-changing commands — dry-run unless the invocation ends with --confirm.
GATED = {"send", "reply"}


def out(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def die(msg: str, code: int = 1) -> None:
    out({"error": msg})
    sys.exit(code)


def load_token() -> str:
    tok = os.environ.get("DISCORD_USER_TOKEN")
    if not tok:
        die("DISCORD_USER_TOKEN is not set — connect Discord (User Token) at "
            "https://auth.acedata.cloud/user/connections, then retry.")
    return tok.strip()


def proxy() -> str | None:
    return (
        os.environ.get("DISCORD_PROXY")
        or os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        or os.environ.get("ALL_PROXY") or os.environ.get("all_proxy")
        or None
    )


def channel_id(args) -> int:
    try:
        return int(args.channel)
    except (TypeError, ValueError):
        die("--channel must be a numeric Discord channel id")


def guild_id(args) -> int:
    try:
        return int(args.guild)
    except (TypeError, ValueError):
        die("--guild must be a numeric Discord guild (server) id")


async def messageable_channel(client, args):
    """Fetch a channel and confirm it can hold messages (not a category/forum)."""
    import discord.abc
    ch = await client.fetch_channel(channel_id(args))
    if not isinstance(ch, discord.abc.Messageable):
        die(f"channel {ch.id} is a {ch.type} channel, which can't hold messages — "
            "pass a text/voice channel id (see `channels --guild <id>`)")
    return ch


# ── commands ──────────────────────────────────────────────────────────────
async def cmd_whoami(client, args):
    u = client.user
    out({"id": str(u.id), "username": u.name, "global_name": getattr(u, "global_name", None),
         "bot": u.bot})


async def cmd_guilds(client, args):
    guilds = await client.fetch_guilds(with_counts=True)
    out([{"id": str(g.id), "name": g.name,
          "members": getattr(g, "approximate_member_count", None)} for g in guilds])


async def cmd_channels(client, args):
    import discord
    guild = await client.fetch_guild(guild_id(args))
    channels = await guild.fetch_channels()
    text = [c for c in channels if isinstance(c, (discord.TextChannel,))]
    out([{"id": str(c.id), "name": c.name, "type": str(c.type)} for c in text])


async def cmd_messages(client, args):
    ch = await messageable_channel(client, args)
    msgs = [m async for m in ch.history(limit=args.limit)]
    out([{"id": str(m.id), "author": m.author.name, "author_id": str(m.author.id),
          "ts": m.created_at, "content": m.content} for m in msgs])


async def cmd_send(client, args):
    ch = await messageable_channel(client, args)
    if not CONFIRM:
        out({"dry_run": True, "would_send": {"channel": str(ch.id),
             "channel_name": getattr(ch, "name", None), "text": args.text},
             "hint": "re-run with a trailing --confirm to actually send"})
        return
    msg = await ch.send(args.text)
    out({"sent": True, "channel": str(ch.id), "message_id": str(msg.id)})


async def cmd_reply(client, args):
    import discord
    ch = await messageable_channel(client, args)
    try:
        target = int(args.message)
    except (TypeError, ValueError):
        die("--message must be a numeric Discord message id")
    if not CONFIRM:
        out({"dry_run": True, "would_reply": {"channel": str(ch.id),
             "reply_to": str(target), "text": args.text},
             "hint": "re-run with a trailing --confirm to actually send"})
        return
    ref = discord.MessageReference(message_id=target, channel_id=ch.id,
                                   guild_id=getattr(ch, "guild", None) and ch.guild.id)
    msg = await ch.send(args.text, reference=ref)
    out({"sent": True, "channel": str(ch.id), "message_id": str(msg.id),
         "reply_to": str(target)})


HANDLERS = {
    "whoami": cmd_whoami, "guilds": cmd_guilds, "channels": cmd_channels,
    "messages": cmd_messages, "send": cmd_send, "reply": cmd_reply,
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="discord_user.py", description="Discord user-token CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("whoami", help="verify the token and show the logged-in account")
    sub.add_parser("guilds", help="list the servers (guilds) the account is in")

    sp = sub.add_parser("channels", help="list text channels in a server")
    sp.add_argument("--guild", required=True)

    sp = sub.add_parser("messages", help="read recent messages in a channel")
    sp.add_argument("--channel", required=True)
    sp.add_argument("--limit", type=int, default=20)

    sp = sub.add_parser("send", help="send a message to a channel (GATED by trailing --confirm)")
    sp.add_argument("--channel", required=True)
    sp.add_argument("--text", required=True)

    sp = sub.add_parser("reply", help="reply to a message (GATED by trailing --confirm)")
    sp.add_argument("--channel", required=True)
    sp.add_argument("--message", required=True)
    sp.add_argument("--text", required=True)
    return p


async def run(args) -> None:
    import discord
    client = discord.Client(proxy=proxy())
    try:
        await client.login(load_token())
        await HANDLERS[args.cmd](client, args)
    finally:
        # close() is safe even if login() failed (no session opened).
        await client.close()


def main() -> None:
    args = build_parser().parse_args(ARGV)
    if args.cmd in GATED and not CONFIRM:
        # Still resolve the channel for the dry-run preview, but never write.
        pass
    try:
        import discord
        from discord.errors import (
            LoginFailure, Forbidden, NotFound, HTTPException,
        )
    except Exception as e:  # discord.py-self not importable
        die(f"discord.py-self is not available in the sandbox image: {e}. "
            "Deploy the sandbox skill dependencies image; do not pip-install it at runtime.")
    try:
        asyncio.run(run(args))
    except LoginFailure as e:
        die("auth failed — the Discord user token is wrong or expired. Reconnect "
            f"at https://auth.acedata.cloud/user/connections. ({e})")
    except Forbidden as e:
        die(f"forbidden by Discord (no access to that channel/server, or blocked): {e}")
    except NotFound as e:
        die(f"not found — check the channel / guild / message id: {e}")
    except HTTPException as e:
        # 429 rate limits and other API errors land here.
        status = getattr(e, "status", None)
        if status == 429:
            retry = getattr(e, "retry_after", None)
            die(f"rate limited by Discord — wait {retry or 'a bit'}s and retry; never parallelize. ({e})")
        die(f"Discord API error (HTTP {status}): {e}")
    except Exception as e:
        die(f"Discord request failed ({type(e).__name__}: {e}). Likely an expired "
            "token — reconnect at https://auth.acedata.cloud/user/connections.")


if __name__ == "__main__":
    main()
