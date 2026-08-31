---
name: discord
description: Work with the user's Discord account through their deployed Discord Agent Proxy. List servers, channels, members, and messages; send, edit, delete, search, react, pin, and send DMs.
when_to_use: |
  Trigger for operations on the user's connected Discord Agent Proxy: inspect
  their account, servers, channels, members, or messages; or send, edit,
  delete, search, react to, pin, or directly message through that account.
connections: [discord]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "2.1"
---

# Discord Agent Proxy

Use the user's deployed Discord Agent Proxy, not Discord's public API directly.
It exposes their account through REST and MCP. The proxy URL and access token
are supplied by the application configuration; treat the token as secret and
never print it. All protected requests need `Authorization: <proxy-token>`.

`/health` and `/readyz` require no token. Check `/health` to verify the HTTP
process and `/readyz` to verify the Discord Gateway connection before making
requests. `/readyz` returns `{"status":"ready","gateway_ready":true}` when
ready; a connection failure returns 503 while the proxy retries.

```sh
BASE="https://discord-bot-xxxxxxxxxxxx.app.acedata.cloud"
curl -sS "$BASE/health"
curl -sS "$BASE/readyz"
curl -sS -H "Authorization: $DISCORD_TOKEN" "$BASE/api/whoami"
```

Successful REST responses are `{"data": ...}` and failures are
`{"error":"..."}`. Never put the token in a URL. A 401 means the proxy token
is invalid; 503 means the token is not configured or the Discord connection is
not ready; 403/404 means the account lacks access or an ID is wrong; on 429,
respect `retry_after` and do not parallelize retries.

## Read

```sh
# Servers, then a server's channels or members
curl -sS -H "Authorization: $DISCORD_TOKEN" "$BASE/api/guilds"
curl -sS -H "Authorization: $DISCORD_TOKEN" \
  "$BASE/api/guilds/$GUILD_ID/channels"
curl -sS -H "Authorization: $DISCORD_TOKEN" \
  "$BASE/api/guilds/$GUILD_ID/members?limit=100"

# Recent messages (default 50, maximum 100) or search (q is required)
curl -sS -H "Authorization: $DISCORD_TOKEN" \
  "$BASE/api/channels/$CHANNEL_ID/messages?limit=20"
curl -sS -H "Authorization: $DISCORD_TOKEN" \
  --get --data-urlencode "q=release date" \
  "$BASE/api/channels/$CHANNEL_ID/messages/search"
```

## Write

Confirm the exact target and content with the user before any write. For a
send retry, reuse the same unique `Idempotency-Key`; the proxy deduplicates its
recent in-memory records, but callers must retain long-term delivery state.

```sh
# Send, optionally replying with "reply_to"
curl -sS -X POST -H "Authorization: $DISCORD_TOKEN" \
  -H "Content-Type: application/json" -H "Idempotency-Key: $OPERATION_ID" \
  "$BASE/api/messages" \
  -d '{"channel_id":"1234567890","content":"Hello","reply_to":"9876543210"}'

# Create a text channel, edit/delete a message, react, or pin
curl -sS -X POST -H "Authorization: $DISCORD_TOKEN" \
  -H "Content-Type: application/json" "$BASE/api/guilds/$GUILD_ID/channels" \
  -d '{"name":"project-discussion"}'
curl -sS -X PATCH -H "Authorization: $DISCORD_TOKEN" \
  -H "Content-Type: application/json" "$BASE/api/channels/$CHANNEL_ID/messages/$MESSAGE_ID" \
  -d '{"content":"Updated"}'
curl -sS -X DELETE -H "Authorization: $DISCORD_TOKEN" \
  "$BASE/api/channels/$CHANNEL_ID/messages/$MESSAGE_ID"
curl -sS -X POST -H "Authorization: $DISCORD_TOKEN" \
  -H "Content-Type: application/json" \
  "$BASE/api/channels/$CHANNEL_ID/messages/$MESSAGE_ID/reactions" -d '{"emoji":"👍"}'
curl -sS -X POST -H "Authorization: $DISCORD_TOKEN" \
  "$BASE/api/channels/$CHANNEL_ID/messages/$MESSAGE_ID/pin"
```

For one-to-one DMs, use `POST /api/dms` with `{"recipient_id":"..."}` to open
a channel, or `POST /api/dms/send` with `{"recipient_id":"...","content":"..."}`.
Only message a recipient after their explicit consent; never enumerate members
for outreach or bulk-send.

## MCP

Connect clients that support static headers to `$BASE/mcp` using
`Authorization: <proxy-token>`. The MCP tools mirror the REST operations:
`discord_whoami`, `discord_list_guilds`, `discord_list_channels`,
`discord_create_text_channel`, `discord_list_members`, `discord_read_messages`,
`discord_search_messages`, `discord_send_message`, `discord_edit_message`,
`discord_delete_message`, `discord_add_reaction`, `discord_pin_message`,
`discord_create_dm`, and `discord_send_dm`.
