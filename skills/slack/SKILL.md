---
name: slack
description: Send messages, search history, and manage channels via Slack's Web API. Use when the user mentions Slack, a channel, a DM, or wants to post to a specific user/group.
when_to_use: |
  Trigger when the user wants to read or write something in Slack —
  send a message to a channel/DM, search history, list channels,
  upload a file, etc.
connections: [slack]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

There is no first-party Slack CLI fit for daily use, so we drive the
[Slack Web API](https://api.slack.com/methods) with `curl + jq`. The
user's OAuth bearer token is in `$SLACK_TOKEN`; every call needs it as
`Authorization: Bearer $SLACK_TOKEN`.

The Slack API ALWAYS returns 200 — check the JSON `ok` field for success.
A failed call has `{"ok": false, "error": "<reason>"}`. Surface the
`error` value verbatim to the user when it occurs.

**Always start with `auth.test`** to confirm the connection works AND
to learn what bot user / team you're posting as. Many subsequent calls
need the bot's user id (`auth.test` returns `user_id`).

## Recipes

### Verify auth (always run first)

```sh
curl -sS -H "Authorization: Bearer $SLACK_TOKEN" \
  https://slack.com/api/auth.test
# {"ok": true, "team": "...", "team_id": "...", "user": "<bot>", "user_id": "U..."}
```

### Resolve a channel name to its ID (you'll need this a lot)

```sh
curl -sS -H "Authorization: Bearer $SLACK_TOKEN" \
  "https://slack.com/api/conversations.list?limit=1000&types=public_channel,private_channel" \
  | jq -r --arg name "general" '.channels[] | select(.name == $name) | .id'
```

### Post a message

```sh
curl -sS -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "$(jq -nc \
        --arg ch "C0123456789" \
        --arg text "Deploy complete." \
        '{channel:$ch, text:$text}')"
```

### Reply in a thread

```sh
curl -sS -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "$(jq -nc \
        --arg ch "C0123456789" \
        --arg ts "1777656720.123456" \
        --arg text "Thanks!" \
        '{channel:$ch, thread_ts:$ts, text:$text}')"
```

### Search messages

```sh
curl -sS -G \
  -H "Authorization: Bearer $SLACK_TOKEN" \
  "https://slack.com/api/search.messages" \
  --data-urlencode "query=in:#engineering deploy" \
  --data-urlencode "count=20"
```

### Send a DM to a user (by email)

```sh
USER_ID=$(curl -sS -G -H "Authorization: Bearer $SLACK_TOKEN" \
  "https://slack.com/api/users.lookupByEmail" \
  --data-urlencode "email=alice@example.com" \
  | jq -r '.user.id')

# DM channels are auto-created the first time you postMessage to a user id.
curl -sS -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "$(jq -nc --arg ch "$USER_ID" --arg text "Hi from the bot." '{channel:$ch, text:$text}')"
```

### Upload a file to a channel

Two-step: create an upload URL, then complete.

```sh
UPLOAD=$(curl -sS -G -H "Authorization: Bearer $SLACK_TOKEN" \
  "https://slack.com/api/files.getUploadURLExternal" \
  --data-urlencode "filename=report.pdf" \
  --data-urlencode "length=$(wc -c < report.pdf)")
URL=$(echo "$UPLOAD" | jq -r '.upload_url')
ID=$(echo "$UPLOAD" | jq -r '.file_id')

curl -sS -T report.pdf "$URL"

curl -sS -X POST https://slack.com/api/files.completeUploadExternal \
  -H "Authorization: Bearer $SLACK_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "$(jq -nc --arg fid "$ID" --arg ch "C0123456789" \
        '{files:[{id:$fid, title:"report.pdf"}], channel_id:$ch}')"
```

## Notes

- **`chat.postMessage` to a public channel requires the bot to be a
  member of that channel.** If you get `not_in_channel`, call
  `conversations.join` first (which also takes the channel id), then
  retry. Private channels and DMs need a manual invite — ask the user.
- Always check `.ok` on the JSON response. `not_authed` / `invalid_auth`
  → ask the user to re-authorize at `auth.acedata.cloud/user/connections`.
- Channel ids start with `C` (channels), `D` (DMs), `G` (private). Don't
  invent ids — always look them up via `conversations.list` or
  `users.lookupByEmail`.
- Slack rate-limits aggressively; `Retry-After` is in the response
  headers if you get a 429. Sleep and retry rather than parallelizing.
