---
name: slack
description: Read channels, messages, canvases, and public-channel search results through a connected Slack workspace.
when_to_use: |
  Use when the user wants to find or summarize Slack content that the
  connected app can access. The connector is read-only.
connections: [slack]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.1"
---

Use the [Slack Web API](https://api.slack.com/methods) with the connected
bot token in `$SLACK_TOKEN`. Send it only to `https://slack.com/api/` over
HTTPS. Check the JSON `ok` field and HTTP status for every response; report
Slack's error value when a call fails. Respect `Retry-After` on HTTP 429.

This app has read-only bot scopes. It cannot post messages, upload files, join
channels, or read arbitrary conversations between other users. Channel and
conversation history is available only where the app has been added. Public
channel search uses `search:read.public`; do not imply that it searches
private channels or direct messages.

## Verify the connected workspace

```sh
curl -sS -H "Authorization: Bearer $SLACK_TOKEN" \
  https://slack.com/api/auth.test
```

Use the returned team and bot user to check that the connection targets the
workspace the user intended.

## List channels visible to the app

```sh
curl -sS -G -H "Authorization: Bearer $SLACK_TOKEN" \
  https://slack.com/api/conversations.list \
  --data-urlencode "types=public_channel,private_channel" \
  --data-urlencode "limit=200"
```

Follow `response_metadata.next_cursor` to paginate. Resolve channel names
to IDs from this response rather than inventing IDs.

## Read channel history or a thread

```sh
curl -sS -G -H "Authorization: Bearer $SLACK_TOKEN" \
  https://slack.com/api/conversations.history \
  --data-urlencode "channel=C0123456789" \
  --data-urlencode "limit=100"

curl -sS -G -H "Authorization: Bearer $SLACK_TOKEN" \
  https://slack.com/api/conversations.replies \
  --data-urlencode "channel=C0123456789" \
  --data-urlencode "ts=1777656720.123456"
```

Read a private channel or direct message only if the app is a member. If
Slack returns `not_in_channel` or `channel_not_found`, ask the user to add
the app to that conversation. Do not try to join it automatically.

## Search public-channel messages

```sh
curl -sS -G -H "Authorization: Bearer $SLACK_TOKEN" \
  https://slack.com/api/search.messages \
  --data-urlencode "query=in:#engineering deploy" \
  --data-urlencode "count=20"
```

If the API reports `missing_scope`, report that result rather than claiming
the search succeeded. The current connection cannot search private channels
or direct messages.

## Resolve a member

```sh
curl -sS -G -H "Authorization: Bearer $SLACK_TOKEN" \
  https://slack.com/api/users.lookupByEmail \
  --data-urlencode "email=alice@example.com"
```

Use member details only to identify people in retrieved content. Never send
an email or message from this read-only connection. If `auth.test` returns
`not_authed` or `invalid_auth`, ask the user to reconnect Slack at
`https://studio.acedata.cloud/console/connectors`.
