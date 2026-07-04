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
  version: "1.2"
---

We drive **personal** Telegram over MTProto with [Telethon](https://docs.telethon.dev/) —
this acts as the user's own account (a "userbot"), so unlike the Bot API it can read full
history, list every conversation, and act on anyone the user can reach.

Credentials are injected as env vars by the connector:

- `TELEGRAM_API_ID` — app id
- `TELEGRAM_API_HASH` — app hash — **secret, never echo**
- `TELEGRAM_SESSION_STRING` — Telethon `StringSession` = **full account access. Never log,
  echo, or print it.** Treat it like the account password.

## CLI

The skill ships [`scripts/tg.py`](scripts/tg.py) — self-contained (the only third-party dep is
`telethon`, preinstalled in the sandbox). Point a var at the shipped path and call it; no heredoc
to re-create per turn, so a multi-step flow (dry-run → confirm) can't lose the helper between calls:

```sh
TG="$SKILL_DIR/scripts/tg.py"
python3 "$TG" whoami
```

Every state-changing command (`send`, `reply`, `send-file`, `forward`, `edit`, `delete`,
`react`, `mark-read`) is **gated**: without a trailing `--confirm` it only DRY-RUNS (prints what
it would do, changes nothing). Read commands run directly. `--confirm` is honored **only as the
last argument** so a message/caption that merely contains "--confirm" can never silently confirm.

## Verify the connection first

```sh
python3 "$TG" whoami
# → {"id": 8367450178, "username": "GermeyAce", "name": "Germey", "phone": "..."}
```

On an auth/session error the stored session is dead — tell the user to reconnect at
https://auth.acedata.cloud/user/connections.

## Read recipes

| Goal | Command |
|---|---|
| Recent conversations | `python3 "$TG" list-chats 20` |
| Only chats with unread (ranked) | `python3 "$TG" unread` |
| A chat's history (oldest→newest) | `python3 "$TG" get-messages <target> 50` |
| Search inside one chat | `python3 "$TG" search <target> "kw" 30` |
| Search across ALL chats | `python3 "$TG" search-global "kw" 30` |
| List contacts | `python3 "$TG" contacts` |
| Info about a chat/user | `python3 "$TG" chat-info <target>` |
| t.me link to a message | `python3 "$TG" message-link <target> <msg_id>` |

`<target>` = numeric id (most reliable — from `list-chats`), `@username`, phone, or exact chat
name. In message rows, `out:true` = sent by the user; `media:true` = has an attachment.

**Summarize-unread pattern**: `unread` → pick the chats that matter → `get-messages <id> N` on
each → summarize. Don't dump 20k messages; sample the most-unread / most-relevant.

## Media

```sh
# Download an attachment from a message → returns the saved path
python3 "$TG" download-media <target> <msg_id> ./tg_downloads
# Send a local file OR an http(s) URL (optional caption) — GATED
python3 "$TG" send-file <target> /path/or/https-url "caption" --confirm
```

An `http(s)` URL is downloaded to a real local file first (with the right
extension from the URL / `Content-Type`) and then uploaded, so a remote image
lands as a **photo** — not a document, and not a silent failure. This is the
reliable way to "发图": pass the CDN URL straight to `send-file`.

To hand a downloaded file back to the user as a link, upload it to the CDN (see the
`cos-upload` skill) after `download-media`.

## Write recipes — all GATED (dry-run unless trailing `--confirm`)

Sending/editing/deleting acts as the **real user**. Always run the dry run first, show the user
exactly what will happen, get an explicit "yes", then re-run with `--confirm` as the **last
argument**. Never bulk-send.

```sh
python3 "$TG" send    <target> "text"                          # → dry_run; add --confirm to send
python3 "$TG" reply   <target> <msg_id> "text" --confirm
python3 "$TG" forward <from_target> <msg_id> <to_target> --confirm
python3 "$TG" edit    <target> <msg_id> "new text" --confirm   # own messages
python3 "$TG" delete  <target> <msg_id> --confirm              # destructive
python3 "$TG" react   <target> <msg_id> "👍" --confirm
python3 "$TG" mark-read <target> --confirm                     # sends read receipts
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
