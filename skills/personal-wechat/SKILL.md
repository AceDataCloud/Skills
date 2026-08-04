---
name: personal-wechat
description: Operate the user's personal WeChat account through their self-hosted Wisdom service (BYOC) — check status, list contacts/conversations, read messages, poll for new ones, search contacts, browse Moments, and (after explicit confirmation) send messages with real @-mentions, post or delete Moments, and manage group chats. Use when the user mentions 个人微信, 我的微信, WeChat personal chat, 微信聊天记录, 微信联系人, 微信群, 朋友圈, reading/summarizing WeChat messages, or sending a WeChat message.
when_to_use: |
  Trigger for the user's personal WeChat account via their own Wisdom server:
  check status/account, list contacts, list conversations, read or summarize a
  chat, poll for new messages, search contacts, browse Moments, send a message
  (with real @-mentions, quote-replies, or media), publish/delete a Moment, or
  create/invite/remove/rename a group. This acts on the user's real desktop
  WeChat, so every write is gated behind explicit confirmation.
connections: [personalwechat]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.1"
---

# Personal WeChat via Wisdom

Use the user's self-hosted **Wisdom** service to operate their personal WeChat
account. Wisdom runs on a Windows host with WeChat Desktop logged in and exposes
an HTTP API.

Credentials are injected by the `personalwechat` BYOC connector:

- `PERSONALWECHAT_BASE_URL` — Wisdom server base URL, e.g. `http://203.0.113.10:8000`.
- `PERSONALWECHAT_API_TOKEN` — Wisdom `API_TOKEN`. Secret — never echo, print, or log it.

The helper sends the token as `Authorization: Bearer ...`; it never puts the
token in the URL. Wisdom answers every UI-driven action (search, send, Moments,
groups) with `202` + a task ID; the helper polls `/api/tasks/{id}` for you and
prints only the final result.

This is the user's **real personal WeChat account**. Read operations run
directly. Every write — send, Moment, group change — dry-runs first and only
executes after the user explicitly approves that exact payload.

## CLI

The skill ships a stdlib-only helper. **Run this resolver at the top of every
Bash block below** — each Bash call is a fresh shell, and `$SKILL_DIR` points at
the LAST skill loaded this turn, so anchor on our own script:

```bash
WX="$SKILL_DIR/scripts/personal_wechat.py"; [ -f "$WX" ] || WX=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/personal_wechat.py' 2>/dev/null | head -1)
[ -f "$WX" ] || { echo "personal-wechat script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }
```

## Verify Connection First

Always start with status when the user asks to use WeChat:

```bash
python3 $WX status
```

Expected healthy shape:

```json
{"status":"ready","since":"…","wechat_running":true,"logged_in":true,"error":null}
```

`/api/status` is the **single** source of truth for connectivity. Judge it by
`status`, `wechat_running` and `logged_in` — nothing else.

| Symptom | Meaning |
|---|---|
| `status: "ready"`, `logged_in: true` | Healthy — proceed. |
| `status: "qr_scan"` / `logged_in: false` | Ask the user to open the Wisdom web UI / RDP and scan the WeChat QR code. |
| `status: "preparing"` | The decrypted DB snapshot is still being built. Wait and retry; reads may fail until it finishes. |
| `status: "error"` | Report `error.code` / `error.message` to the user. |
| HTTP 401 | Ask the user to reconnect the Personal WeChat connector with the current Wisdom API token. |
| Connection refused / timeout | Ask the user to check the Windows host, security group, and port 8000. |

Never infer "WeChat is offline" from a 404 on some other path — a 404 means that
route does not exist on this Wisdom version, not that the account is logged out.

## Read Workflows

### Current Account

```bash
python3 $WX account
```

### Contacts

```bash
python3 $WX contacts --limit 50
python3 $WX contacts --type group --limit 100
python3 $WX contacts --limit 100 --offset 100
```

`--limit` is clamped to 200 per page (Wisdom's ceiling). Page with `--offset`
rather than asking for a bigger limit.

### Conversations

```bash
python3 $WX conversations --limit 20
```

Each entry's `id` is what `messages` takes as `conversation_id`. This reads the
decrypted WeChat database directly and already covers full history — there is no
separate "history" endpoint.

### Messages in a Conversation

```bash
python3 $WX messages "CONVERSATION_ID" --limit 50 --order asc
python3 $WX messages "CONVERSATION_ID" --limit 50 --offset 50
```

Output includes `mentions`, `quoted_text` and `conversation_type`, so you can see
who was @-mentioned and what a 引用 reply was replying to.

### New Messages Since a Timestamp

```bash
python3 $WX poll --since 1785000000 --limit 100
```

`--since` is a Unix timestamp in seconds. Use this to catch up after a gap
instead of re-reading a whole conversation.

### Moments (朋友圈)

```bash
python3 $WX moments --limit 30
python3 $WX moments --limit 30 --self-only
```

This is a synced view cache, so a just-deleted post may linger until WeChat
re-syncs.

### Tasks

Inspect queued/finished UI tasks when a write seems stuck:

```bash
python3 $WX tasks --limit 20
python3 $WX task TASK_ID
```

## Search

```bash
python3 $WX search "Alice"
```

Search drives the WeChat UI, so it is slower than the local DB reads above. Use
it to confirm a target exists before sending.

## Writes — ALL GATED

Every write command below dry-runs by default, printing the exact payload it
would submit. It executes only with `--confirm`, or with `--unattended-confirm`
when an AceDataCloud scheduled task pre-authorized this Skill.

Show the dry-run to the user, get explicit approval of the exact target and
content, then re-run with `--confirm`. Never put `--confirm` in the first
attempt. Never infer consent from vague text.

### Send a Message

```bash
python3 $WX send "Alice" "今晚 8 点开会吗？"
# -> {"dry_run": true, "action": "send", ...}
python3 $WX send "Alice" "今晚 8 点开会吗？" --confirm
```

**Real @-mentions in a group.** Pass `--mention` (repeatable) — Wisdom drives
WeChat's own mention popover, producing a genuine @-notification. Do NOT type
`@Name` into the message text and hope; that is inert text that notifies nobody.

```bash
python3 $WX send "项目群" "记得今天交周报" --mention "Doms Jay" --confirm
python3 $WX send "项目群" "记得今天交周报" --mention "Alice" --mention "Bob" --confirm
python3 $WX send "项目群" "全员通知" --mention-all --confirm     # owner/admin only
```

The send result echoes `mentions`. If it comes back `null` after you passed
`--mention`, the mention did not register — tell the user instead of claiming
the @ succeeded.

**Quote-reply.** Replies to the newest message in that chat whose text matches:

```bash
python3 $WX send "Alice" "这个我来跟" --quote-text "这个 bug 谁跟一下" --confirm
```

`--quote-text` takes precedence over mentions, and falls back to a plain send if
no matching message is found.

**Media.** Wisdom downloads the URL on the Windows host and sends the file:

```bash
python3 $WX send "Alice" --type image --image-url https://example.com/a.png --confirm
python3 $WX send "Alice" --type video --video-url https://example.com/a.mp4 --confirm
python3 $WX send "Alice" --type file  --file-url  https://example.com/a.pdf --confirm
```

**Retries.** A send whose outcome you never saw may still have been delivered.
When retrying, pass the same `--idempotency-key` so Wisdom returns the original
task instead of sending twice:

```bash
python3 $WX send "Alice" "hi" --idempotency-key daily-2026-08-04 --confirm
```

### Moments (朋友圈)

```bash
python3 $WX moment-post "今天上线了新功能"
python3 $WX moment-post "看看这张图" --image-url https://example.com/a.png --visibility public --confirm
```

`--visibility` is `public` / `private` / `partial` / `exclude`
(公开 / 私密 / 部分可见 / 不给谁看), defaulting to `public`.

Deleting is **irreversible**. `match` must be a distinctive substring of one of
the user's own Moments; Wisdom refuses ambiguous matches rather than guessing:

```bash
python3 $WX moment-delete "Veo Videos Generation API"
python3 $WX moment-delete "Veo Videos Generation API" --confirm
```

### Group Chats

These are visible to other people — always confirm the exact member list first.

```bash
python3 $WX group-create "Alice" "Bob" --name "项目群" --confirm   # needs >= 2 members
python3 $WX group-invite "项目群" "Carol" --confirm
python3 $WX group-remove "项目群" "Carol" --confirm                # kicks; visible to the group
python3 $WX group-rename "项目群" "项目群 2026" --confirm           # renames for everyone
```

### Scheduled-task unattended confirmation

When running inside an AceDataCloud scheduled task, the platform may pre-authorize
specific Skills for unattended execution. If all of these are true:

- `AICHAT_UNATTENDED_MODE=true`
- `AICHAT_ACTIVE_SKILL` is `personal-wechat` or `acedatacloud/personal-wechat`
- `AICHAT_ACTIVE_SKILL` appears in `AICHAT_UNATTENDED_ALLOWED_SKILLS`

then the user has pre-authorized this Skill for that scheduled task. In that
case, use `--unattended-confirm` in place of `--confirm`:

```bash
python3 $WX send "Alice" "今晚 8 点开会吗？" --unattended-confirm
```

If the helper returns `unattended_confirmation_denied`, do not retry with
`--confirm`; report the dry-run and explain that the task needs this Skill to be
selected in its unattended authorization settings.

## Safety Rules

- Never print `PERSONALWECHAT_API_TOKEN`.
- Treat `PERSONALWECHAT_BASE_URL + API_TOKEN` as full remote control of the user's WeChat.
- Dry-run every write first, ask for explicit approval, then re-run with `--confirm`.
- Use `--unattended-confirm` only when the platform env says this Skill is pre-authorized.
- Group and Moment writes are visible to other people; `moment-delete` is irreversible.
- Report what actually happened. If `mentions` came back `null`, the @ did not register.
- Do not call restart/logout endpoints unless the user explicitly asks to repair the service.
- Judge connectivity only by `python3 $WX status`. A 404 on another path means that route
  does not exist, not that WeChat is offline.

## Endpoint Mapping

The helper wraps these Wisdom endpoints:

| Command | Endpoint |
|---|---|
| `status` | `GET /api/status` |
| `account` | `GET /api/account` |
| `contacts` | `GET /api/contacts` |
| `conversations` | `GET /api/conversations` |
| `messages` | `GET /api/messages` |
| `poll` | `GET /api/messages/poll` |
| `moments` | `GET /api/moments` |
| `tasks` / `task` | `GET /api/tasks`, `GET /api/tasks/{id}` |
| `search` | `POST /api/search` |
| `send` | `POST /api/messages/send` |
| `moment-post` / `moment-delete` | `POST /api/moments`, `DELETE /api/moments` |
| `group-create` / `-invite` / `-remove` / `-rename` | `POST /api/groups`, `/invite`, `/remove`, `/rename` |

Everything from `search` down is a queued UI task (`202` + task ID); the write
ones additionally need `--confirm` or a verified `--unattended-confirm`.
