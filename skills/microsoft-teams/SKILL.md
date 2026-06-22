---
name: microsoft-teams
description: Read and send Microsoft Teams chat messages via Microsoft Graph v1.0. Use when the user mentions Microsoft Teams chats, a 1:1 or group chat, reading recent Teams messages, or sending a Teams chat message. (Channel messages are not covered — they need admin-consented scopes.)
when_to_use: |
  Trigger when the user wants to list their Teams chats, read recent
  messages in a chat, or send a chat message. Scoped to **chats**
  (1:1 / group) which use delegated `Chat.Read` / `Chat.ReadWrite` /
  `ChatMessage.Send` — no admin consent. Confirm before sending; do
  not attempt channel-message reads (different, admin-gated scopes).
connections: [microsoft/teams]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Drive **Microsoft Teams chats** via Microsoft Graph with `curl + jq`. The user's
OAuth bearer token is in `$MICROSOFT_TEAMS_TOKEN`; every call needs
`Authorization: Bearer $MICROSOFT_TEAMS_TOKEN`. Base URL:
`https://graph.microsoft.com/v1.0`.

Failures are `{"error":{"code","message"}}` — show `message` verbatim. `401` =
re-install. `403`/`Forbidden` on send = the user granted read-only
(`Chat.Read`) → re-connect with `Chat.ReadWrite` + `ChatMessage.Send`.

```bash
G="https://graph.microsoft.com/v1.0"; AUTH="Authorization: Bearer $MICROSOFT_TEAMS_TOKEN"
# My chats (1:1 + group), most recent first; expand members for names
curl -sS -H "$AUTH" "$G/me/chats?\$top=20&\$expand=members" \
  | jq '.value[] | {id, chatType, topic, members: [.members[].displayName]}'
```

## Read & send chat messages

```bash
CHAT="CHAT_ID"
# Recent messages
curl -sS -H "$AUTH" "$G/chats/$CHAT/messages?\$top=20" \
  | jq '.value[] | {from: .from.user.displayName, created: .createdDateTime, text: .body.content}'

# Send a message (confirm content with the user first). contentType html|text.
curl -sS -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"body":{"contentType":"html","content":"Hi from the assistant 👋"}}' \
  "$G/chats/$CHAT/messages" | jq '{id, created: .createdDateTime}'
```

## Gotchas

- **Chats only.** Reading Teams **channel** messages needs
  `ChannelMessage.Read.All` — a Microsoft "protected API" requiring tenant-admin
  consent — which this connector deliberately does not request. Don't try
  `/teams/{id}/channels/.../messages`; it will 403.
- `body.content` for HTML messages contains markup — strip tags when
  summarizing.
- OData `$top`/`$expand` need the `$` escaped in the shell; quote the URL.
