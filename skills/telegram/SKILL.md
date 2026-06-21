---
name: telegram
description: Read, search and send personal Telegram messages — list recent chats / contacts / groups, pull a conversation's history, search messages, and send a message — driven by the Telethon MTProto client with the user's own account. Use when the user mentions Telegram, a Telegram chat/group/contact, "我的 Telegram", reading or replying to Telegram messages, or summarizing Telegram conversations.
when_to_use: |
  Trigger when the user wants to do anything with their personal Telegram
  account: list recent conversations, read / summarize the history of a chat
  or group, search their messages for a keyword, look up a contact, or send /
  reply to a message. This drives the user's OWN account over MTProto (not a
  bot), so it can see everything the user can see.
connections: [telegram]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

We drive **personal** Telegram over the MTProto protocol with the
[Telethon](https://docs.telethon.dev/) Python library — this acts as the user's own
account (a "userbot"), so unlike the Bot API it can read full chat history, list every
conversation, and message anyone the user can message.

The user's credentials are injected as environment variables by the connector:

- `TELEGRAM_API_ID` — the app id (from my.telegram.org)
- `TELEGRAM_API_HASH` — the app hash — **secret, never echo it**
- `TELEGRAM_SESSION_STRING` — a Telethon `StringSession` = **full account access. Never log,
  echo, or print it.** Treat it like the account password.

## Setup — write the helper once per session

`telethon` is preinstalled in the sandbox image. The helper is written to `./tg.py` **in the
current working directory** (the per-session workdir) — not a shared global path like `/tmp` —
so concurrent sessions never race on or reuse each other's file.

```sh
# telethon is preinstalled; the `|| pip install` is a best-effort fallback only
# (the sandbox is non-root, so a runtime install may not succeed — rely on the
# preinstalled package).
python3 -c "import telethon" 2>/dev/null || pip install --user --quiet telethon 2>/dev/null || true

cat > ./tg.py <<'PY'
import os, sys, json, asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
SESSION = os.environ["TELEGRAM_SESSION_STRING"]


async def resolve(client, target):
    # Accept a numeric id, @username, phone, or an exact chat display name.
    try:
        return await client.get_entity(int(target))
    except (ValueError, TypeError):
        pass
    try:
        return await client.get_entity(target)
    except Exception:
        async for d in client.iter_dialogs():
            if d.name == target:
                return d.entity
        raise ValueError(f"could not resolve target: {target}")


async def main():
    cmd = sys.argv[1]
    async with TelegramClient(StringSession(SESSION), API_ID, API_HASH) as client:
        if cmd == "whoami":
            me = await client.get_me()
            print(json.dumps({"id": me.id, "username": me.username,
                              "name": ((me.first_name or "") + " " + (me.last_name or "")).strip()},
                             ensure_ascii=False))
        elif cmd == "list-chats":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            out = []
            async for d in client.iter_dialogs(limit=limit):
                out.append({"name": d.name, "id": d.id, "group": d.is_group,
                            "channel": d.is_channel, "user": d.is_user, "unread": d.unread_count})
            print(json.dumps(out, ensure_ascii=False))
        elif cmd == "get-messages":
            target = sys.argv[2]
            n = int(sys.argv[3]) if len(sys.argv) > 3 else 50
            ent = await resolve(client, target)
            out = []
            async for m in client.iter_messages(ent, limit=n):
                out.append({"id": m.id, "date": str(m.date), "out": m.out,
                            "sender_id": m.sender_id, "text": m.message})
            out.reverse()
            print(json.dumps(out, ensure_ascii=False))
        elif cmd == "search":
            target, query = sys.argv[2], sys.argv[3]
            n = int(sys.argv[4]) if len(sys.argv) > 4 else 30
            ent = await resolve(client, target)
            out = []
            async for m in client.iter_messages(ent, search=query, limit=n):
                out.append({"id": m.id, "date": str(m.date), "sender_id": m.sender_id, "text": m.message})
            print(json.dumps(out, ensure_ascii=False))
        elif cmd == "send":
            # Gated: without --confirm this only DRY-RUNS (prints the intended
            # target + text and sends nothing). Pass --confirm to actually send.
            target, text = sys.argv[2], sys.argv[3]
            confirm = "--confirm" in sys.argv[4:]
            ent = await resolve(client, target)
            if not confirm:
                name = getattr(ent, "title", None) or getattr(ent, "first_name", None) or str(target)
                print(json.dumps({"dry_run": True, "would_send_to": name, "text": text,
                                  "note": "re-run with --confirm to actually send"}, ensure_ascii=False))
                return
            msg = await client.send_message(ent, text)
            print(json.dumps({"sent": True, "id": msg.id}, ensure_ascii=False))
        else:
            print(json.dumps({"error": f"unknown command: {cmd}"}))
            sys.exit(1)


asyncio.run(main())
PY
echo "helper ready"
```

## Verify the connection (run this first)

```sh
python3 ./tg.py whoami
# → {"id": 8367450178, "username": "GermeyAce", "name": "Germey"}
```

If this errors with an auth/session message, the stored session is dead (revoked or expired) —
tell the user to reconnect the Telegram connector at https://auth.acedata.cloud/user/connections.

## Recipes

### List recent conversations

```sh
python3 ./tg.py list-chats 20
# → [{"name":"Ace <> ConduitOS","id":-5287630726,"group":true,...,"unread":0}, ...]
```

Use the returned `id` (or the exact `name`) as the target for the next calls.

### Read a conversation's history (oldest→newest)

```sh
# target = numeric id, @username, phone, or exact chat name; second arg = how many messages
python3 ./tg.py get-messages -5287630726 50
python3 ./tg.py get-messages @some_username 30
```

`out: true` means the message was sent BY the user; `sender_id` is the author. Summarize from
the returned JSON.

### Search inside a conversation

```sh
python3 ./tg.py search -5287630726 "keyword" 30
```

(Server-side search is scoped to one chat. To search broadly, list chats first, then search the
relevant ones.)

### Send / reply to a message — TWO-STEP, confirm first

Sending posts a **real message as the user**, so it is gated:

```sh
# Step 1 — DRY RUN (default, sends nothing). Show this preview to the user.
python3 ./tg.py send -5287630726 "Hi, following up on this."
# → {"dry_run": true, "would_send_to": "Ace <> ConduitOS", "text": "Hi, following up on this.", ...}

# Step 2 — only after the user explicitly says yes in the conversation, add --confirm:
python3 ./tg.py send -5287630726 "Hi, following up on this." --confirm
# → {"sent": true, "id": 4502}
```

**Always run the dry run first, show the user exactly who + what, and require an explicit "yes"
before re-running with `--confirm`** — even if the original instruction said "just send it".
Never bulk-send.

## Gotchas — surface these before the user is surprised

- **This is the user's real account.** Sending posts as them; reading exposes all their private
  chats. Be conservative.
- **`FloodWaitError`**: Telegram rate-limits userbots. If a call fails with a flood-wait of N
  seconds, tell the user to retry after N seconds — do not loop/retry aggressively (it escalates
  toward an account ban).
- **Dead session**: a `session_string` can be revoked by the user from Telegram → Settings →
  Devices. On an `AuthKeyError` / unauthorized error, the fix is reconnecting the connector, not
  retrying.
- **Never print `TELEGRAM_SESSION_STRING` or `TELEGRAM_API_HASH`** — they are full-account
  secrets. The helper never prints them; keep it that way.
- **Resolving targets**: prefer the numeric `id` from `list-chats` (most reliable). Names work
  only on an exact match; usernames need the leading `@`.
