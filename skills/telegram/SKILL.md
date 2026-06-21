---
name: telegram
description: Full personal Telegram control over MTProto (Telethon) with the user's own account — list/search chats, read & summarize history, see unread, look up contacts & chat info, download media, and send / reply / forward / edit / delete / react / send files / mark read. Use when the user mentions Telegram, a Telegram chat/group/contact, "我的 Telegram", reading/replying/forwarding/summarizing Telegram messages, their unread Telegram, or sending a file/message on Telegram.
when_to_use: |
  Trigger for anything on the user's personal Telegram account: list recent
  conversations or just the unread ones, read / summarize a chat or group,
  search one chat or across all chats, look up a contact or a chat's info,
  download a photo/file from a message, or take an action — send, reply,
  forward, edit, delete, react, send a file, or mark a chat read. This drives
  the user's OWN account over MTProto (not a bot), so it sees everything they see.
connections: [telegram]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.1"
---

We drive **personal** Telegram over MTProto with [Telethon](https://docs.telethon.dev/) —
this acts as the user's own account (a "userbot"), so unlike the Bot API it can read full
history, list every conversation, and act on anyone the user can reach.

Credentials are injected as env vars by the connector:

- `TELEGRAM_API_ID` — app id
- `TELEGRAM_API_HASH` — app hash — **secret, never echo**
- `TELEGRAM_SESSION_STRING` — Telethon `StringSession` = **full account access. Never log,
  echo, or print it.** Treat it like the account password.

## Setup — write the helper once per session

`telethon` is preinstalled in the sandbox. The helper is written to `./tg.py` **in the current
working directory** (the per-session workdir) — not a shared global path — so concurrent
sessions never race.

Every state-changing command (`send`, `reply`, `send-file`, `forward`, `edit`, `delete`,
`react`, `mark-read`) is **gated**: without a trailing `--confirm` it only DRY-RUNS (prints what
it would do, changes nothing). Read commands run directly. `--confirm` is honored **only as the
last argument** so a message/caption that merely contains "--confirm" can never silently confirm.

```sh
python3 -c "import telethon" 2>/dev/null || pip install --user --quiet telethon 2>/dev/null || true

cat > ./tg.py <<'PY'
import os, sys, json, asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl import functions
from telethon.tl.types import ReactionEmoji

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
SESSION = os.environ["TELEGRAM_SESSION_STRING"]

_raw = sys.argv[1:]
# --confirm is only honored as the LAST token, and only one is stripped, so a
# message/caption that merely contains "--confirm" cannot silently confirm a write.
CONFIRM = bool(_raw) and _raw[-1] == "--confirm"
a = _raw[:-1] if CONFIRM else list(_raw)
cmd = a[0] if a else "help"
args = a[1:]
GATED = {"send", "reply", "send-file", "forward", "edit", "delete", "react", "mark-read"}


def out(o):
    print(json.dumps(o, ensure_ascii=False, default=str))


async def resolve(client, target):
    # 1) try direct resolve; 2) fall back to scanning dialogs by id or exact name
    #    (StringSession doesn't persist the entity cache, so a numeric id from a
    #    previous invocation may need the dialog scan to recover its access hash).
    for attempt in (lambda: client.get_entity(int(target)), lambda: client.get_entity(target)):
        try:
            return await attempt()
        except Exception:
            pass
    ti = None
    try:
        ti = int(target)
    except (ValueError, TypeError):
        pass
    async for d in client.iter_dialogs():
        if (ti is not None and d.id == ti) or d.name == target:
            return d.entity
    raise ValueError(f"could not resolve target: {target}")


def msg_row(m):
    return {"id": m.id, "date": str(m.date), "out": m.out, "sender_id": m.sender_id,
            "text": m.message, "media": bool(m.media)}


def need(n):
    if len(args) < n:
        raise ValueError(f"{cmd} needs {n} argument(s), got {len(args)}")


async def run():
    if cmd in GATED and not CONFIRM:
        out({"dry_run": True, "command": cmd, "args": args,
             "note": "re-run with --confirm as the LAST argument to actually perform this write"})
        return
    async with TelegramClient(StringSession(SESSION), API_ID, API_HASH) as cl:
        if cmd == "whoami":
            me = await cl.get_me()
            out({"id": me.id, "username": me.username,
                 "name": ((me.first_name or "") + " " + (me.last_name or "")).strip(), "phone": me.phone})

        elif cmd == "list-chats":
            limit = int(args[0]) if args and args[0].lstrip("-").isdigit() else 20
            unread_only = "unread-only" in args
            res = []
            async for d in cl.iter_dialogs(limit=limit):
                if unread_only and not d.unread_count:
                    continue
                res.append({"name": d.name, "id": d.id, "group": d.is_group,
                            "channel": d.is_channel, "user": d.is_user, "unread": d.unread_count})
            out(res)

        elif cmd == "unread":
            res = []
            async for d in cl.iter_dialogs():
                if d.unread_count:
                    res.append({"name": d.name, "id": d.id, "unread": d.unread_count,
                                "group": d.is_group, "channel": d.is_channel})
            out(sorted(res, key=lambda x: -x["unread"]))

        elif cmd == "get-messages":
            need(1); ent = await resolve(cl, args[0])
            n = int(args[1]) if len(args) > 1 else 50
            rows = [msg_row(m) async for m in cl.iter_messages(ent, limit=n)]
            rows.reverse()
            out(rows)

        elif cmd == "search":
            need(2); ent = await resolve(cl, args[0])
            q = args[1]; n = int(args[2]) if len(args) > 2 else 30
            out([msg_row(m) async for m in cl.iter_messages(ent, search=q, limit=n)])

        elif cmd == "search-global":
            need(1); q = args[0]; n = int(args[1]) if len(args) > 1 else 30
            rows = []
            async for m in cl.iter_messages(None, search=q, limit=n):
                r = msg_row(m); r["chat_id"] = m.chat_id
                rows.append(r)
            out(rows)

        elif cmd == "contacts":
            res = await cl(functions.contacts.GetContactsRequest(hash=0))
            out([{"id": u.id, "username": u.username,
                  "name": ((u.first_name or "") + " " + (u.last_name or "")).strip(), "phone": u.phone}
                 for u in res.users])

        elif cmd == "chat-info":
            need(1); ent = await resolve(cl, args[0])
            info = {"id": ent.id, "type": type(ent).__name__,
                    "title": getattr(ent, "title", None),
                    "name": ((getattr(ent, "first_name", "") or "") + " " + (getattr(ent, "last_name", "") or "")).strip() or None,
                    "username": getattr(ent, "username", None)}
            try:
                info["participants"] = (await cl.get_participants(ent, limit=1)).total
            except Exception:
                pass
            out(info)

        elif cmd == "message-link":
            need(2); ent = await resolve(cl, args[0]); mid = int(args[1])
            try:
                r = await cl(functions.channels.ExportMessageLinkRequest(channel=ent, id=mid))
                out({"link": r.link})
            except Exception as e:
                out({"error": f"links only available for channels/supergroups: {e}"})

        elif cmd == "download-media":
            need(2); ent = await resolve(cl, args[0]); mid = int(args[1])
            outdir = args[2] if len(args) > 2 else "./tg_downloads"
            os.makedirs(outdir, exist_ok=True)
            m = await cl.get_messages(ent, ids=mid)
            if not m or not m.media:
                out({"error": "no media on that message"}); return
            path = await cl.download_media(m, file=outdir)
            out({"downloaded": path})

        # ---- gated writes (need trailing --confirm) ----
        elif cmd == "send":
            need(2); ent = await resolve(cl, args[0])
            m = await cl.send_message(ent, args[1])
            out({"sent": True, "id": m.id})

        elif cmd == "reply":
            need(3); ent = await resolve(cl, args[0])
            m = await cl.send_message(ent, args[2], reply_to=int(args[1]))
            out({"sent": True, "id": m.id, "reply_to": int(args[1])})

        elif cmd == "send-file":
            need(2); ent = await resolve(cl, args[0])
            caption = args[2] if len(args) > 2 else None
            m = await cl.send_file(ent, args[1], caption=caption)
            out({"sent": True, "id": m.id})

        elif cmd == "forward":
            need(3); src = await resolve(cl, args[0]); mid = int(args[1]); dst = await resolve(cl, args[2])
            fwd = await cl.forward_messages(dst, mid, src)
            out({"forwarded": True, "id": getattr(fwd, "id", None) or [x.id for x in fwd]})

        elif cmd == "edit":
            need(3); ent = await resolve(cl, args[0])
            m = await cl.edit_message(ent, int(args[1]), args[2])
            out({"edited": True, "id": m.id})

        elif cmd == "delete":
            need(2); ent = await resolve(cl, args[0])
            await cl.delete_messages(ent, int(args[1]))
            out({"deleted": True, "id": int(args[1])})

        elif cmd == "react":
            need(3); ent = await resolve(cl, args[0]); mid = int(args[1]); emoji = args[2]
            await cl(functions.messages.SendReactionRequest(
                peer=ent, msg_id=mid, reaction=[ReactionEmoji(emoticon=emoji)]))
            out({"reacted": True, "id": mid, "emoji": emoji})

        elif cmd == "mark-read":
            need(1); ent = await resolve(cl, args[0])
            await cl.send_read_acknowledge(ent)
            out({"marked_read": True})

        else:
            out({"error": f"unknown command: {cmd}"}); sys.exit(1)


async def main():
    try:
        await run()
    except SystemExit:
        raise
    except Exception as e:
        out({"error": f"{type(e).__name__}: {e}"})
        sys.exit(1)


asyncio.run(main())
PY
echo "helper ready"
```

## Verify the connection first

```sh
python3 ./tg.py whoami
# → {"id": 8367450178, "username": "GermeyAce", "name": "Germey", "phone": "..."}
```

On an auth/session error the stored session is dead — tell the user to reconnect at
https://auth.acedata.cloud/user/connections.

## Read recipes

| Goal | Command |
|---|---|
| Recent conversations | `python3 ./tg.py list-chats 20` |
| Only chats with unread (ranked) | `python3 ./tg.py unread` |
| A chat's history (oldest→newest) | `python3 ./tg.py get-messages <target> 50` |
| Search inside one chat | `python3 ./tg.py search <target> "kw" 30` |
| Search across ALL chats | `python3 ./tg.py search-global "kw" 30` |
| List contacts | `python3 ./tg.py contacts` |
| Info about a chat/user | `python3 ./tg.py chat-info <target>` |
| t.me link to a message | `python3 ./tg.py message-link <target> <msg_id>` |

`<target>` = numeric id (most reliable — from `list-chats`), `@username`, phone, or exact chat
name. In message rows, `out:true` = sent by the user; `media:true` = has an attachment.

**Summarize-unread pattern**: `unread` → pick the chats that matter → `get-messages <id> N` on
each → summarize. Don't dump 20k messages; sample the most-unread / most-relevant.

## Media

```sh
# Download an attachment from a message → returns the saved path
python3 ./tg.py download-media <target> <msg_id> ./tg_downloads
# Send a local file or a URL (optional caption) — GATED
python3 ./tg.py send-file <target> /path/or/https-url "caption" --confirm
```

To hand a downloaded file back to the user as a link, upload it to the CDN (see the
`cos-upload` skill) after `download-media`.

## Write recipes — all GATED (dry-run unless trailing `--confirm`)

Sending/editing/deleting acts as the **real user**. Always run the dry run first, show the user
exactly what will happen, get an explicit "yes", then re-run with `--confirm` as the **last
argument**. Never bulk-send.

```sh
python3 ./tg.py send    <target> "text"                          # → dry_run; add --confirm to send
python3 ./tg.py reply   <target> <msg_id> "text" --confirm
python3 ./tg.py forward <from_target> <msg_id> <to_target> --confirm
python3 ./tg.py edit    <target> <msg_id> "new text" --confirm   # own messages
python3 ./tg.py delete  <target> <msg_id> --confirm              # destructive
python3 ./tg.py react   <target> <msg_id> "👍" --confirm
python3 ./tg.py mark-read <target> --confirm                     # sends read receipts
```

The dry run returns `{"dry_run": true, "command": ..., "args": [...]}` — present that to the
user verbatim as the confirmation prompt.

## Gotchas — surface before the user is surprised

- **This is the user's real account.** Confirm before any write; reading exposes private chats.
- **`FloodWaitError`**: Telegram rate-limits userbots. On a flood-wait of N seconds, tell the
  user to retry after N — never loop/retry aggressively (escalates toward a ban).
- **Dead session**: revoked from Telegram → Settings → Devices, or ~6-month inactivity. On
  `AuthKeyError`/unauthorized, reconnect the connector (don't retry).
- **Never print `TELEGRAM_SESSION_STRING` / `TELEGRAM_API_HASH`** — full-account secrets.
- **Targets**: prefer the numeric `id` from `list-chats` (the helper recovers its access hash by
  scanning dialogs); names need an exact match, usernames need a leading `@`.
- **`message-link`** only works for public channels/supergroups; private 1:1 / basic groups
  return an error (no shareable link exists).
- **`edit`/`delete`** generally only apply to the user's own messages (admins can delete others
  in groups they manage).
