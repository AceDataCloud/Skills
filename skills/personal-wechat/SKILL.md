---
name: personal-wechat
description: Operate the user's personal WeChat account through their self-hosted Wisdom service (BYOC) — check login status, list contacts/conversations, read and summarize history, search contacts, refresh the local history DB, and send messages only after explicit confirmation. Use when the user mentions 个人微信, 我的微信, WeChat personal chat, 微信聊天记录, 微信联系人, reading/summarizing WeChat messages, or sending a WeChat message.
when_to_use: |
  Trigger for the user's personal WeChat account via their own Wisdom server:
  check status/account, list contacts, list recent conversations, read or
  summarize a chat, query local history, search contacts, or send a message.
  This acts on the user's real desktop WeChat, so writes are gated behind
  explicit confirmation.
connections: [personalwechat]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# Personal WeChat via Wisdom

Use the user's self-hosted **Wisdom** service to operate their personal WeChat
account. Wisdom runs on a Windows host with WeChat Desktop logged in and exposes
an HTTP API.

Credentials are injected by the `personalwechat` BYOC connector:

- `PERSONALWECHAT_BASE_URL` — Wisdom server base URL, e.g. `http://82.156.126.14:8000`.
- `PERSONALWECHAT_API_TOKEN` — Wisdom `API_TOKEN`. Secret — never echo, print, or log it.

The helper sends the token as `Authorization: Bearer ...`; it never puts the
token in the URL.

This is the user's **real personal WeChat account**. Read operations can run
directly. Sending messages or files must be dry-run first, then performed only
after the user explicitly approves the exact target and content.

## CLI

The skill ships a stdlib-only helper:

```bash
WX=$SKILL_DIR/scripts/personal_wechat.py
```

## Verify Connection First

Always start with status when the user asks to use WeChat:

```bash
python3 $WX status
```

Expected healthy shape:

```json
{"auth":{"logged_in":true,"wechat_running":true,"page":"logged_in"}}
```

If `logged_in=false`, tell the user to open the Wisdom web UI / RDP and scan the
WeChat QR code. If the API returns 401, ask the user to reconnect the Personal
WeChat connector with the current Wisdom API token.

## Read Workflows

### Current Account

```bash
python3 $WX account
```

### Contacts

```bash
python3 $WX contacts --limit 50
```

### Recent Conversations

Use the normal conversations endpoint first; it prefers WeChat DB when ready and
falls back to Wisdom's app DB.

```bash
python3 $WX conversations --limit 20
```

For decrypted local WeChat history sessions:

```bash
python3 $WX conversations --history --limit 20
```

### Messages in a Conversation

First list conversations, then use the `id` as `conversation_id`:

```bash
python3 $WX messages "34642176898@chatroom" --limit 50 --order asc
```

### Historical Messages

Read from Wisdom's decrypted WeChat local databases:

```bash
python3 $WX history --limit 50
python3 $WX history --talker "34642176898@chatroom" --limit 50
python3 $WX history --limit 20 --offset 20
```

### Raw SQL, Read-Only Only

Wisdom permits only `SELECT` and `PRAGMA`:

```bash
python3 $WX sql MicroMsg.db 'SELECT count(*) AS cnt FROM Session'
```

Use raw SQL only for diagnostics or targeted metadata queries. Do not dump large
message tables unless the user explicitly asks.

### Refresh History DB

If history looks stale, refresh the decrypted DB snapshot:

```bash
python3 $WX refresh-history
```

## Search

```bash
python3 $WX search "Alice"
```

Search drives the WeChat UI, so it may be slower than local DB history reads.

## Sending Messages — GATED

`send` dry-runs by default. It never sends unless `--confirm` is present, or
unless an AceDataCloud scheduled task pre-authorized this Skill and you use
`--unattended-confirm`.

```bash
python3 $WX send "Alice" "今晚 8 点开会吗？"
# -> {"dry_run": true, ...}
```

Show the dry-run output to the user and ask for explicit approval of the exact
recipient and text. Only then run:

```bash
python3 $WX send "Alice" "今晚 8 点开会吗？" --confirm
```

Never add `--confirm` in the first attempt. Never infer consent from vague text.
The user must clearly approve sending this exact message.

### Scheduled-task unattended confirmation

When running inside an AceDataCloud scheduled task, the platform may pre-authorize
specific Skills for unattended execution. If all of these are true:

- `AICHAT_UNATTENDED_MODE=true`
- `AICHAT_ACTIVE_SKILL` is `personal-wechat` or `acedatacloud/personal-wechat`
- `AICHAT_ACTIVE_SKILL` appears in `AICHAT_UNATTENDED_ALLOWED_SKILLS`

then the user has pre-authorized this Skill for that scheduled task. In that
case, use:

```bash
python3 $WX send "Alice" "今晚 8 点开会吗？" --unattended-confirm
```

If the helper returns `unattended_confirmation_denied`, do not retry with
`--confirm`; report the dry-run and explain that the task needs this Skill to be
selected in its unattended authorization settings.

## Safety Rules

- Never print `PERSONALWECHAT_API_TOKEN`.
- Treat `PERSONALWECHAT_BASE_URL + API_TOKEN` as full remote control of the user's WeChat.
- For normal chat write/send operations: dry-run first, ask for explicit approval, then re-run with `--confirm`.
- For scheduled-task unattended writes: use `--unattended-confirm` only when the platform env says this Skill is pre-authorized.
- Do not call logout/restart endpoints from the skill unless the user explicitly asks to repair the Wisdom service.
- If Wisdom returns 503 for history, run `python3 $WX refresh-history` once, then retry the read.
- If the server is unreachable, ask the user to check the Windows host / security group / port 8000.

## Endpoint Mapping

The helper wraps these Wisdom endpoints:

- `GET /api/status`
- `GET /api/auth/status`
- `GET /api/account`
- `GET /api/contacts?version=2.0`
- `GET /api/conversations`
- `GET /api/conversations/history`
- `GET /api/messages`
- `GET /api/messages/history`
- `POST /api/messages/history/query`
- `POST /api/messages/history/refresh`
- `POST /api/search`
- `POST /api/messages/send` (only after `--confirm` or verified `--unattended-confirm`)
