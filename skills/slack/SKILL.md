---
name: slack
description: Search Slack public channels, read joined conversations, and send user-confirmed bot messages.
when_to_use: |
  Use when the user wants to search public Slack channels, read or summarize
  conversations the app has joined, or send a message as the connected bot.
connections: [slack]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.4"
---

Use the [Slack Web API](https://api.slack.com/methods) with the connected
bot token in `$SLACK_TOKEN` for joined-channel reads and confirmed sends.
Use the separate user token in `$SLACK_USER_TOKEN` only for public-channel
search. Send either token only to `https://slack.com/api/` over HTTPS. Check
the JSON `ok` field and HTTP status for every response; report Slack's
error value when a call fails. Respect `Retry-After` on HTTP 429.

Messages are sent as the AceDataCloud bot, not as the user's Slack account.
The app cannot upload files or join channels. Bot channel and conversation
history is available only where the app has been added. Public search covers
public channels in the authorized user's workspace, including channels the
bot has not joined; it does not cover private channels or direct messages.
The bot token cannot use Slack's legacy `search.messages` method and cannot
use Real-time Search without a Slack event `action_token`. Never use the user
token to post a message.

## Search public-channel messages

Use Slack's Real-time Search API for a user-initiated public search. If
`$SLACK_USER_TOKEN` is absent, explain that the Slack connection needs
re-authorization for public search at
`https://studio.acedata.cloud/console/connectors`; do not silently substitute
a recent-history scan. Keep `channel_types` explicitly limited to
`public_channel` and `content_types` to `messages`. Request at most 20 results
per page, follow `next_cursor` only as needed, and give the user message
permalinks as sources. Do not persist Slack search results outside the
current task.

```sh
QUERY="deployment issue"
curl -sS -X POST https://slack.com/api/assistant.search.context \
  -H "Authorization: Bearer $SLACK_USER_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "$(jq -nc --arg q "$QUERY" \
    '{query:$q, channel_types:["public_channel"], content_types:["messages"], limit:20}')" \
  | jq '{ok, error, next_cursor, messages: [.results.messages[]? | {content, author_name, channel_name, message_ts, permalink}]}'
```

If Slack returns an error, report that error rather than presenting an empty
result as a successful search. Search results are limited to the authorized
user's public-channel access and Slack's search ranking and retention rules.

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
  --data-urlencode "limit=15"

curl -sS -G -H "Authorization: Bearer $SLACK_TOKEN" \
  https://slack.com/api/conversations.replies \
  --data-urlencode "channel=C0123456789" \
  --data-urlencode "ts=1777656720.123456"
```

Read a private channel or direct message only if the app is a member. If
Slack returns `not_in_channel` or `channel_not_found`, ask the user to add
the app to that conversation. Do not try to join it automatically.

## Find a keyword in one joined private channel or direct message

For a private channel or direct message that the bot has joined, fetch only
that conversation's recent history and filter locally. This is a bounded
recent-history scan, not Slack's public search. State the time window and
whether older messages remain unread. On new installs of
commercial apps outside the Slack Marketplace, Slack may limit
`conversations.history` to one call per minute with at most 15 messages;
respect `Retry-After` and do not fan out across channels.

```sh
KEYWORD="deploy"
curl -sS -G -H "Authorization: Bearer $SLACK_TOKEN" \
  https://slack.com/api/conversations.history \
  --data-urlencode "channel=C0123456789" \
  --data-urlencode "limit=15" \
  | jq --arg q "$KEYWORD" '{ok, error, has_more, matches: [.messages[]? | select((.text // "") | contains($q)) | {ts, user, text}]}'
```

If Slack returns an error, report it rather than claiming the search
succeeded. An empty match list is only a result for the messages fetched,
not proof that the keyword is absent from the channel's full history.

## Resolve a member

```sh
curl -sS -G -H "Authorization: Bearer $SLACK_TOKEN" \
  https://slack.com/api/users.lookupByEmail \
  --data-urlencode "email=alice@example.com"
```

Use member details only to identify people in retrieved content. Do not send
unsolicited direct messages or enumerate members for outreach.

## Send a message or thread reply

Before each send, resolve the exact workspace, channel or existing
conversation, and final message text. Call `request_action_confirmation`
with `kind: "generic"` and show those three values. Send only if the user
confirms. If the confirmation tool is unavailable, return a draft. If this
is an unattended run, send only when the saved task already authorizes that
exact destination and content; otherwise return a draft.

The bot must already be a member of the target channel or conversation.
If Slack returns `not_in_channel` or `channel_not_found`, ask the user
to add the app there. Do not call `conversations.join`. Do not retry a
`chat.postMessage` request whose outcome is unknown; first check the
channel history to avoid duplicates.

```sh
curl -sS -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "$(jq -nc --arg ch "C0123456789" --arg text "Confirmed message" \
    '{channel:$ch, text:$text}')"
```

For a reply in an existing thread, include its exact `thread_ts` in the
payload. Check `ok`, `channel`, and `ts` in the response and report the
sent message link or channel and timestamp.

If `auth.test` returns `not_authed` or `invalid_auth`, ask the user to
reconnect Slack at `https://studio.acedata.cloud/console/connectors`.
