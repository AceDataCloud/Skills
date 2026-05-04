---
name: google-gmail
description: Read, search and triage Gmail mail / threads / labels / attachments via the Gmail v1 REST API. Use when the user mentions Gmail, "my inbox", unread mail, recent emails from someone, summarising a thread, downloading an attachment, or finding mail by label / query.
when_to_use: |
  Trigger when the user wants to read, list, search, summarise or
  inspect Gmail mail — including triaging the inbox, surfacing unread,
  pulling a single thread for review, or downloading an attachment.
  The installed connector grants read-only scope (`gmail.readonly`);
  sending / replying / archiving / labelling are out of scope.
connections: [google/gmail]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Drive Gmail via `curl + jq`. The user's OAuth bearer token is in
`$GOOGLE_GMAIL_TOKEN`; every call needs it as
`Authorization: Bearer $GOOGLE_GMAIL_TOKEN`. The token already
carries the `gmail.readonly` scope the user agreed to at install plus
the identity scopes (`openid email profile`).

The Gmail API returns standard JSON; failures surface as
`{"error": {"code": 401|403|..., "message": "..."}}` — show that
error verbatim. `401` means the token expired (re-install). `403`
or `400 insufficientPermissions` means the user is asking for a write
this connector cannot satisfy — say so.

**Always start with `users/me/profile`** to confirm the connection works
AND learn which Gmail account you're operating against. Mailbox payloads
can be huge — fetch metadata first, only `format=full` when the user
actually wants the body of a specific message.

## Recipes

### Verify auth (always run first)

```sh
curl -sS -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
  "https://gmail.googleapis.com/gmail/v1/users/me/profile" \
  | jq '{email: .emailAddress, totalMessages, totalThreads, historyId}'
```

### List recent unread inbox

```sh
curl -sS -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
  --get "https://gmail.googleapis.com/gmail/v1/users/me/messages" \
  --data-urlencode 'q=is:unread in:inbox newer_than:7d' \
  --data-urlencode 'maxResults=20' \
  | jq '.messages[]'
```

The `messages.list` endpoint returns only `{id, threadId}` — you have
to fan out to `messages.get` for headers / body. Cheap pattern: list
ids → get with `format=metadata&metadataHeaders=From,Subject,Date` for
each. Use `format=full` only if the user wants the body.

### List + enrich with headers (one-shot inbox triage)

```sh
IDS=$(curl -sS -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
  --get "https://gmail.googleapis.com/gmail/v1/users/me/messages" \
  --data-urlencode 'q=is:unread in:inbox' \
  --data-urlencode 'maxResults=10' \
  | jq -r '.messages[].id')

for ID in $IDS; do
  curl -sS -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
    --get "https://gmail.googleapis.com/gmail/v1/users/me/messages/$ID" \
    --data-urlencode 'format=metadata' \
    --data-urlencode 'metadataHeaders=From' \
    --data-urlencode 'metadataHeaders=Subject' \
    --data-urlencode 'metadataHeaders=Date' \
    | jq '{id: .id, snippet: .snippet, headers: (.payload.headers | map({(.name): .value}) | add), labels: .labelIds}'
done | jq -s '.'
```

### Read a single message body (plain text and html)

```sh
ID='18f1a2b3c4d5e6f0'
RESP=$(curl -sS -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
  --get "https://gmail.googleapis.com/gmail/v1/users/me/messages/$ID" \
  --data-urlencode 'format=full')

echo "$RESP" | jq '{id, snippet, headers: (.payload.headers | map({(.name): .value}) | add)}'

# Body is base64url-encoded inside payload.parts[].body.data — Gmail
# splits multipart messages, so collect every text/plain or text/html
# leaf and base64url-decode them.
echo "$RESP" | jq -r '
  def walk(p):
    if (p.parts // null) then (p.parts | map(walk(.)) | add) else [p] end;
  walk(.payload)
  | map(select(.mimeType=="text/plain" and (.body.data // "") != ""))
  | .[].body.data' \
  | tr '_-' '/+' | base64 -d 2>/dev/null
```

If the plain-text leaf is empty, fall back to the `text/html` leaf
(same walk, swap the mimeType filter) and tell the user it's HTML.

### Read a whole thread

```sh
THREAD_ID='18f1a2b3c4d5e6f0'
curl -sS -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
  --get "https://gmail.googleapis.com/gmail/v1/users/me/threads/$THREAD_ID" \
  --data-urlencode 'format=metadata' \
  --data-urlencode 'metadataHeaders=From' \
  --data-urlencode 'metadataHeaders=Subject' \
  --data-urlencode 'metadataHeaders=Date' \
  | jq '{id, historyId, messages: [.messages[] | {id, snippet, from: (.payload.headers | from_entries.From), date: (.payload.headers | from_entries.Date)}]}'
```

### Search by Gmail query

```sh
# Same query DSL the Gmail UI uses: from:, to:, subject:, has:attachment,
# is:unread, label:Work, after:2026/04/01, before:2026/05/01, …
Q='from:boss@example.com subject:OKR newer_than:30d'
curl -sS -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
  --get "https://gmail.googleapis.com/gmail/v1/users/me/messages" \
  --data-urlencode "q=$Q" \
  --data-urlencode 'maxResults=20' \
  | jq '.messages // []'
```

`q` syntax reference: <https://support.google.com/mail/answer/7190> —
the model-friendly bits are `from:`, `to:`, `cc:`, `subject:`, `label:`,
`is:unread`, `is:read`, `is:starred`, `has:attachment`, `filename:pdf`,
`newer_than:7d`, `older_than:30d`, `after:YYYY/MM/DD`, `before:`, `in:inbox`,
`in:trash`. Combine with `OR` / `()` / `-`.

### List labels (system + user-defined)

```sh
curl -sS -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
  "https://gmail.googleapis.com/gmail/v1/users/me/labels" \
  | jq '.labels[] | {id, name, type, color: .color.backgroundColor}'
```

The system labels are `INBOX`, `SENT`, `DRAFT`, `IMPORTANT`, `UNREAD`,
`STARRED`, `SPAM`, `TRASH`, plus `CATEGORY_*` (Personal / Social /
Promotions / Updates / Forums).

### Filter by label

```sh
LABEL_ID='Label_4'  # from labels.list above
curl -sS -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
  --get "https://gmail.googleapis.com/gmail/v1/users/me/messages" \
  --data-urlencode "labelIds=$LABEL_ID" \
  --data-urlencode 'maxResults=20' \
  | jq '.messages // []'
```

Multiple `labelIds` query params behave like AND.

### Download an attachment

```sh
MSG_ID='18f1a2b3c4d5e6f0'

# 1. find the attachment leaf
RESP=$(curl -sS -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
  --get "https://gmail.googleapis.com/gmail/v1/users/me/messages/$MSG_ID" \
  --data-urlencode 'format=full')

echo "$RESP" | jq '
  def walk(p):
    if (p.parts // null) then (p.parts | map(walk(.)) | add) else [p] end;
  walk(.payload)
  | map(select(.body.attachmentId? != null))
  | .[] | {filename, mimeType, attachmentId: .body.attachmentId, size: .body.size}'

# 2. fetch the attachment by id
ATT_ID='ANGjdJ-abc123'
OUT=/tmp/attachment.bin
curl -sS -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
  "https://gmail.googleapis.com/gmail/v1/users/me/messages/$MSG_ID/attachments/$ATT_ID" \
  | jq -r .data | tr '_-' '/+' | base64 -d > "$OUT"
file "$OUT"
```

### Pagination

```sh
PAGE_TOKEN=''
while : ; do
  RESP=$(curl -sS -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
    --get "https://gmail.googleapis.com/gmail/v1/users/me/messages" \
    --data-urlencode 'q=in:inbox' \
    --data-urlencode 'maxResults=100' \
    ${PAGE_TOKEN:+--data-urlencode "pageToken=$PAGE_TOKEN"})
  echo "$RESP" | jq -c '.messages[]?'
  PAGE_TOKEN=$(echo "$RESP" | jq -r '.nextPageToken // empty')
  [ -z "$PAGE_TOKEN" ] && break
done
```

## Common error codes

| HTTP | meaning | what to tell the user |
|---|---|---|
| `401 UNAUTHENTICATED` | token expired / revoked | "Reconnect the Gmail connector on the Connections page." |
| `403 insufficientPermissions` | scope missing | "This connector grants only read access — modifying mail isn't possible." |
| `403 userRateLimitExceeded` / `429` | quota / throttling | back off ~5s, then retry once. |
| `404 notFound` | wrong message / thread / attachment id | double-check the id, or fall back to `messages.list` with the right query. |
| `400 invalidQuery` | malformed `q` | print the `q` you sent + the error back to the user. |

Never log or echo `$GOOGLE_GMAIL_TOKEN` — treat it as a secret.
