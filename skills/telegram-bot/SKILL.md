---
name: telegram-bot
description: Publish to your Telegram channel/group via a bot using the official Telegram Bot API — send text or photo posts, edit and delete messages, and verify the bot's access to a chat. Use when the user wants to broadcast to a Telegram channel/group with a bot token (BotFather), cross-post an article, or manage the bot's posts. Distinct from the personal-account Telegram connector.
when_to_use: |
  Trigger when the user wants a Telegram BOT to post to their channel / group:
  send a text or photo message, edit or delete a message, or check that the bot
  is an admin of the target chat. Auth is a bot token from @BotFather; the bot
  must be an admin (with post rights) in the target channel/group. This acts as
  the bot, so confirm the text and target chat_id before sending publicly.
connections: [telegrambot]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Call the **official Telegram Bot API** with `curl + jq`. The bot token is
injected as `$TELEGRAMBOT_BOT_TOKEN`; an optional default target chat is
`$TELEGRAMBOT_CHAT_ID` (e.g. `@your_channel` or a numeric id). Base URL:
`https://api.telegram.org/bot$TELEGRAMBOT_BOT_TOKEN/<METHOD>`.

Every response is JSON `{"ok":true,"result":...}` on success, or
`{"ok":false,"error_code":<n>,"description":"<msg>"}` on failure — always check
`.ok` and show `description` verbatim. Common failures: `401 Unauthorized` = bad/
revoked token (reconnect the connector), `400 Bad Request: chat not found` = wrong
chat_id, `403 Forbidden: bot is not a member of the channel chat` / `... need
administrator rights` = add the bot to the channel as an admin with post rights,
`429` with `parameters.retry_after` = rate-limited, wait that many seconds.

`chat_id` is `@channelusername` (public) or the numeric id (private channels/
groups, often negative like `-1001234567890`). Resolve/verify it with `getChat`.

## Step 1 — verify the bot + target

```bash
BOT="https://api.telegram.org/bot$TELEGRAMBOT_BOT_TOKEN"
curl -sS "$BOT/getMe" | jq '{ok, bot: .result.username, name: .result.first_name}'
# confirm the bot can post to the target chat (must be admin in the channel):
CHAT="${TELEGRAMBOT_CHAT_ID:-@your_channel}"
curl -sS -G "$BOT/getChat" --data-urlencode "chat_id=$CHAT" \
  | jq '{ok, type: .result.type, title: .result.title, error: .description}'
```

## Send a text post

**Confirm the text and target chat with the user before posting publicly.** Text
is 1-4096 chars. Use `parse_mode=HTML` (simplest) or `MarkdownV2`.

```bash
CHAT="${TELEGRAMBOT_CHAT_ID:-@your_channel}"
curl -sS -G "$BOT/sendMessage" \
  --data-urlencode "chat_id=$CHAT" \
  --data-urlencode "text=<b>Hello</b> from the bot 👋  #ai" \
  --data-urlencode "parse_mode=HTML" \
  --data-urlencode "disable_web_page_preview=false" \
  | jq '{ok, message_id: .result.message_id, error: .description}'
```

The public post URL for a channel is `https://t.me/<channelusername>/<message_id>`.

- **HTML mode** supports `<b> <i> <u> <s> <a href> <code> <pre> <blockquote>`.
  Escape literal `< > &` as `&lt; &gt; &amp;`.
- **MarkdownV2** requires escaping `_ * [ ] ( ) ~ \` > # + - = | { } . !` with `\`.
- Always send `text` via `--data-urlencode` so newlines/Cyrillic/emoji aren't mangled.

## Send a photo with caption

```bash
CHAT="${TELEGRAMBOT_CHAT_ID:-@your_channel}"
curl -sS -G "$BOT/sendPhoto" \
  --data-urlencode "chat_id=$CHAT" \
  --data-urlencode "photo=https://cdn.example.com/pic.jpg" \
  --data-urlencode "caption=<b>Caption</b> text" \
  --data-urlencode "parse_mode=HTML" \
  | jq '{ok, message_id: .result.message_id, error: .description}'
```

`photo` accepts an HTTPS URL (≤5 MB, Telegram fetches it), a Telegram `file_id`,
or an uploaded file. Caption is 0-1024 chars. For an album use `sendMediaGroup`.

## Edit / delete a message

```bash
# edit text (same chat_id + message_id)
curl -sS -G "$BOT/editMessageText" \
  --data-urlencode "chat_id=$CHAT" --data-urlencode "message_id=123" \
  --data-urlencode "text=Updated text" --data-urlencode "parse_mode=HTML" \
  | jq '{ok, error: .description}'

# delete a message
curl -sS -G "$BOT/deleteMessage" \
  --data-urlencode "chat_id=$CHAT" --data-urlencode "message_id=123" \
  | jq '{ok, error: .description}'
```

`deleteMessage` works for the bot's own channel posts within 48 hours (and needs
`can_delete_messages`/post rights).

## Gotchas

- **The bot must be added to the channel/group as an admin** with post rights, or
  sends return `403`. `getChat` first to confirm access.
- Channel numeric ids are large negative numbers (`-100...`); prefer `@username`
  for public channels.
- Free broadcast limit is ~30 msg/s; space out bulk sends or you'll hit `429`
  (respect `parameters.retry_after`).
- This is the **bot** speaking (not your personal account) — for reading your own
  DMs / groups as yourself, use the `telegram` (MTProto) connector instead.
