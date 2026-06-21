---
name: discordbot
description: List channels, read recent messages, and send messages on Discord using the user's own bot, via the Discord REST API. Use when the user wants their Discord BOT to post a message, read a channel, or list servers/channels — anything that acts in a server the bot was invited to.
when_to_use: |
  Trigger when the user wants to send, read, or list things on Discord
  through their bot: list the servers/channels the bot can see, read recent
  messages in a channel, or post / reply in a channel. Messages are sent as
  the BOT, not the user's personal account, and only in servers the bot has
  been invited to with the right permissions.
connections: [discordbot]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
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

**Before sending a message, confirm the exact channel and content with the
user.** Sending is irreversible and public to that channel.

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
  | jq 'map({author: .author.username, ts: .timestamp, content})'
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

## Notes

- A "server" in the UI is a "guild" in the API; messages live in channels
  inside guilds. Always: list guilds → list that guild's channels → act on a
  channel id. Don't invent ids.
- The bot only sees servers it was invited to. To add it: Developer Portal →
  OAuth2 → URL Generator → scope `bot` + the permissions you need → open the
  URL → pick a server (the user needs *Manage Server* there).
- This is a bot, not the user's account — it cannot read the user's DMs or
  the user's full server list, only what the bot itself can access.
- Mentions: `<@USER_ID>` pings a user, `<#CHANNEL_ID>` links a channel. Plain
  text is fine for normal messages.
