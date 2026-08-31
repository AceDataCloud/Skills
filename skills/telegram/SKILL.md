---
name: telegram
description: Work with the user's personal Telegram account through their deployed Telegram Account Proxy. List chats and contacts, read/search messages, and send, edit, delete, react, or mark chats read.
when_to_use: |
  Trigger for operations through the user's Telegram Account Proxy: inspect
  login status, chats, contacts, or messages; or send, edit, delete, react to,
  or mark messages read on their personal account.
connections: [telegram]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.5"
---

# Telegram Account Proxy

Use the user's deployed Telegram Account Proxy. It provides REST and MCP access
to one personal account; it is not the Telegram Bot API. The proxy URL and
access token are supplied by the application configuration. Keep the token
secret and send it only as `Authorization: <proxy-token>`.

`/health` and `/readyz` are unauthenticated. Check `/health` for the HTTP
process and `/readyz` for the MTProto connection before protected operations.
Ready returns `{"status":"ready","gateway_connected":true,...}` even while
login is pending; message operations require `login_state:"authenticated"`.

```sh
BASE="https://telegram-bot-xxxxxxxxxxxx.app.acedata.cloud"
curl -sS "$BASE/health"
curl -sS "$BASE/readyz"
curl -sS -H "Authorization: $TELEGRAM_TOKEN" "$BASE/api/auth/status"
```

All successful responses are `{"data": ...}` and errors are `{"error":"..."}`.
Never put the token in the URL. A 401 means the token is wrong, 503 means the
proxy token is absent or MTProto is not ready, 400 means invalid input, and
403/404 means missing account access or an unknown target. On 429, wait for
`retry_after`; do not retry concurrently.

## Login

Use the console to generate and scan a login QR code. The REST login endpoints
are `POST /api/auth/qr`, `GET /api/auth/status`, `POST /api/auth/password`
with `{"password":"..."}`, and `POST /api/auth/logout`. Treat a two-factor
password as secret. Login states are `login_required`, `waiting_scan`,
`password_required`, and `authenticated`.

## Read

`target` may be a chat ID, username, or exact chat name; prefer an ID if a name
is ambiguous.

```sh
curl -sS -H "Authorization: $TELEGRAM_TOKEN" \
  "$BASE/api/chats?limit=20&unread_only=false"
curl -sS -H "Authorization: $TELEGRAM_TOKEN" "$BASE/api/contacts"
curl -sS -H "Authorization: $TELEGRAM_TOKEN" \
  "$BASE/api/chats/$TARGET/messages?limit=50"
curl -sS -H "Authorization: $TELEGRAM_TOKEN" --get \
  --data-urlencode "q=release date" --data-urlencode "target=$TARGET" \
  "$BASE/api/messages/search"
```

## Write

Confirm the exact target and final content with the user before sending,
editing, deleting, reacting, or marking read. Do not bulk-message or use the
proxy to evade Telegram limits.

```sh
# Send, with optional reply_to
curl -sS -X POST -H "Authorization: $TELEGRAM_TOKEN" \
  -H "Content-Type: application/json" "$BASE/api/messages" \
  -d '{"target":"me","text":"Hello from my Telegram proxy"}'

curl -sS -X PATCH -H "Authorization: $TELEGRAM_TOKEN" \
  -H "Content-Type: application/json" "$BASE/api/chats/$TARGET/messages/$MESSAGE_ID" \
  -d '{"text":"Updated"}'
curl -sS -X DELETE -H "Authorization: $TELEGRAM_TOKEN" \
  "$BASE/api/chats/$TARGET/messages/$MESSAGE_ID"
curl -sS -X POST -H "Authorization: $TELEGRAM_TOKEN" \
  -H "Content-Type: application/json" \
  "$BASE/api/chats/$TARGET/messages/$MESSAGE_ID/reactions" -d '{"emoji":"👍"}'
curl -sS -X POST -H "Authorization: $TELEGRAM_TOKEN" "$BASE/api/chats/$TARGET/read"
```

## MCP

Connect clients that support static headers to `$BASE/mcp` using
`Authorization: <proxy-token>`. The available MCP tools are
`telegram_whoami`, `telegram_list_chats`, `telegram_contacts`,
`telegram_read_messages`, `telegram_search_messages`, `telegram_send_message`,
`telegram_edit_message`, `telegram_delete_message`, `telegram_react`, and
`telegram_mark_read`.
