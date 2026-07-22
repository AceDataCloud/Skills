---
name: discordbot
description: List channels, read recent messages, send channel messages, and send a single user-initiated DM on Discord using the user's own bot via the Discord REST API.
when_to_use: |
  Trigger when the user wants to send, read, or list things on Discord
  through their bot: list the servers/channels the bot can see, read recent
  messages in a channel, post / reply in a channel, or DM one user who has
  explicitly initiated the interaction. Messages are sent as the BOT, not
  the user's personal account, and only where the bot has access.
connections: [discordbot]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.1"
---

We drive the [Discord API](https://discord.com/developers/docs/reference)
with `curl + jq` using the user's **bot** token in `$DISCORDBOT_TOKEN`. The
auth header is `Authorization: Bot $DISCORDBOT_TOKEN` — note the literal
`Bot ` prefix (NOT `Bearer`). Base URL is `https://discord.com/api/v10`.

This acts as the user's registered **bot**, so it can only see and act in
servers (guilds) the bot has been **invited to** and only where it has the
relevant permission (View Channels / Send Messages / Read Message History).
A `403 Forbidden` (code 50001 "Missing Access" / 50013 "Missing
Permissions") almost always means the bot isn't in that server or lacks the
permission — tell the user to invite the bot or grant the permission rather
than retrying.

Errors are JSON `{"code": <n>, "message": "<reason>"}`. A `401` means the
bot token is wrong/reset — ask the user to re-paste it at
`auth.acedata.cloud/user/connections`. A `429` carries `retry_after`
(seconds) — sleep that long, then retry; never parallelize.

## Sending safety

- Before sending, confirm the exact destination and final content with the
  user. Sending is irreversible.
- A DM must be initiated by a recipient action, such as asking the bot for
  details by replying with an advertised keyword. Server membership, a public
  profile, or appearing in a member list is not consent.
- Send to exactly one recipient per invocation. Never enumerate members,
  create DM channels in a loop, or send unsolicited/bulk outreach.
- For an unattended scheduled run, send only when its task definition already
  contains one exact `recipient_id`, `consent_channel_id`,
  `consent_message_id`, `consent_keyword`, and approved `content`. If any is
  missing, return a draft without sending.
- Do not follow up unless the recipient replies. Treat `stop`, `unsubscribe`,
  or an equivalent refusal as a permanent opt-out.

## Recipes

### Verify the bot (always run first)

```sh
curl -sS -H "Authorization: Bot $DISCORDBOT_TOKEN" \
  "https://discord.com/api/v10/users/@me" \
  | jq '{id, username, bot}'
```

### List servers (guilds) the bot is in

```sh
curl -sS -H "Authorization: Bot $DISCORDBOT_TOKEN" \
  "https://discord.com/api/v10/users/@me/guilds" \
  | jq 'map({id, name})'
```

### List text channels in a server

Channel `type` 0 = text, 5 = announcement; 2 = voice, 4 = category (skip
those for messaging). You need a guild id from the call above.

```sh
GUILD_ID="123456789012345678"
curl -sS -H "Authorization: Bot $DISCORDBOT_TOKEN" \
  "https://discord.com/api/v10/guilds/$GUILD_ID/channels" \
  | jq 'map(select(.type==0 or .type==5) | {id, name, type})'
```

### Read recent messages in a channel

Reading message **content** requires the **Message Content Intent** to be
enabled on the bot (Developer Portal → Bot → Privileged Gateway Intents).
Without it, `content` comes back empty for messages that don't mention the
bot. Needs the *Read Message History* permission in that channel.

```sh
CHANNEL_ID="123456789012345678"
curl -sS -H "Authorization: Bot $DISCORDBOT_TOKEN" \
  "https://discord.com/api/v10/channels/$CHANNEL_ID/messages?limit=20" \
  | jq 'map({id, author_id: .author.id, author: .author.username, author_bot: .author.bot, ts: .timestamp, content})'
```

### Send a message to a channel

```sh
CHANNEL_ID="123456789012345678"
curl -sS -X POST \
  -H "Authorization: Bot $DISCORDBOT_TOKEN" \
  -H "Content-Type: application/json" \
  "https://discord.com/api/v10/channels/$CHANNEL_ID/messages" \
  -d "$(jq -nc --arg c "Hello from the bot." '{content: $c}')"
```

### Reply to a specific message

```sh
CHANNEL_ID="123456789012345678"; MESSAGE_ID="987654321098765432"
curl -sS -X POST \
  -H "Authorization: Bot $DISCORDBOT_TOKEN" \
  -H "Content-Type: application/json" \
  "https://discord.com/api/v10/channels/$CHANNEL_ID/messages" \
  -d "$(jq -nc --arg c "On it!" --arg m "$MESSAGE_ID" \
        '{content: $c, message_reference: {message_id: $m}}')"
```

### Send one opt-in DM

Use only after applying every rule in **Sending safety**. The helper fetches
the source message from Discord and verifies that its non-bot author matches
`RECIPIENT_ID` and its complete text matches `CONSENT_KEYWORD`. Do not call the
Create DM endpoint directly. Matching is case-insensitive and collapses
surrounding or repeated whitespace.

```sh
RECIPIENT_ID="123456789012345678"
CONSENT_CHANNEL_ID="223456789012345678"
CONSENT_MESSAGE_ID="323456789012345678"
CONSENT_KEYWORD="details"

python3 "$SKILL_DIR/scripts/discordbot.py" send-opt-in-dm \
  --recipient-id "$RECIPIENT_ID" \
  --consent-channel-id "$CONSENT_CHANNEL_ID" \
  --consent-message-id "$CONSENT_MESSAGE_ID" \
  --consent-keyword "$CONSENT_KEYWORD" \
  --content "Here are the details you requested."
```

The command is a dry-run unless the final argument is `--confirm`. In a
pre-authorized scheduled task, use final `--unattended-confirm` instead. The
helper validates all IDs, verifies the opt-in message, and skips an identical
message already present in the DM history. Discord may block or rate-limit bots
that open many DMs; do not retry by targeting another account.

## Notes

- A "server" in the UI is a "guild" in the API; messages live in channels
  inside guilds. Always: list guilds → list that guild's channels → act on a
  channel id. Don't invent ids.
- The bot only sees servers it was invited to. To add it: Developer Portal →
  OAuth2 → URL Generator → scope `bot` + the permissions you need → open the
  URL → pick a server (the user needs *Manage Server* there).
- This is a bot, not the user's account — it cannot read the user's DMs or
  the user's full server list, only what the bot itself can access.
- A bot can open its own DM channel with one consenting user; that does not
  grant access to the connected user's personal DMs.
- Mentions: `<@USER_ID>` pings a user, `<#CHANNEL_ID>` links a channel. Plain
  text is fine for normal messages.
