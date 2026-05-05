---
name: google-gmail
description: Read, search, triage, label, archive and send Gmail mail / threads / labels / attachments via the Gmail v1 REST API. Use when the user mentions Gmail, "my inbox", unread mail, recent emails from someone, summarising a thread, downloading an attachment, finding mail by label / query, archiving or labelling a thread, or drafting and sending a reply / new message.
when_to_use: |
  Trigger when the user wants to read, list, search, summarise,
  inspect, modify or send Gmail mail — including triaging the inbox,
  surfacing unread, pulling a single thread, downloading an
  attachment, archiving / labelling / trashing messages, or having
  the AI draft and send a reply or new message on their behalf.
  The installed connector always grants `gmail.readonly`; the user
  also opts in to `gmail.modify` (label / archive / trash) and
  `gmail.send` (compose + send) at install time — confirm the action
  is in scope before issuing it.
connections: [google/gmail]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.2"
---

Drive Gmail via `curl + jq`. The user's OAuth bearer token is in
`$GOOGLE_GMAIL_TOKEN`; every call needs it as
`Authorization: Bearer $GOOGLE_GMAIL_TOKEN`. At minimum the token
carries `gmail.readonly` plus the identity scopes
(`openid email profile`); if the user opted in to write at install
time it also carries `gmail.modify` (label / archive / trash) and/or
`gmail.send` (compose + send). Always assume the narrowest scope
until a write actually fails — don't ask Google for new scopes from
here.

The Gmail API returns standard JSON; failures surface as
`{"error": {"code": 401|403|..., "message": "..."}}` — show that
error verbatim. `401` means the token expired (re-install). `403
insufficientPermissions` means the user didn't grant the write scope
this call needs — explain which scope is missing and suggest
re-installing the connector with the matching write box checked.

**Before any destructive write** (trashing a thread, sending an email)
show the user the exact target / draft and ask them to confirm. Don't
fan out across many messages without an explicit go-ahead.

**Always start with `users/me/profile`** to confirm the connection works
AND learn which Gmail account you're operating against. Mailbox payloads
can be huge — fetch metadata first, only `format=full` when the user
actually wants the body of a specific message.

## Optional: Google Workspace CLI (`gws`) for outbound mail

[`gws`](https://github.com/googleworkspace/cli) is Google's official CLI
(not officially supported — community-maintained on the `googleworkspace`
org). It dynamically builds its command surface from Google's Discovery
Document, exits non-zero on API errors, and ships hand-crafted helper
commands (prefixed `+`) that handle the message-encoding boilerplate.

**Use `gws` for sending mail.** The Gmail REST API requires every
outbound message to be a fully-formed RFC 822 message, base64url-encoded
into a `raw` field, with reply / forward threading carried in
`In-Reply-To` / `References` / `threadId`. The `+send / +reply /
+reply-all / +forward` helpers do all of that for you. **For everything
else** (read, search, labels, attachments) `gws` and curl are equivalent,
so the curl recipes below are usually shorter — stay on those.

### Install

```sh
npm install -g @googleworkspace/cli   # or: brew install googleworkspace-cli
# Pre-built binaries also at https://github.com/googleworkspace/cli/releases
gws --version
```

### Auth

`gws` reads its OAuth bearer token from the `GOOGLE_WORKSPACE_CLI_TOKEN`
environment variable. The Gmail token used in this skill is in
`$GOOGLE_GMAIL_TOKEN`, so re-export it once at the top of every shell
block that calls `gws`:

```sh
export GOOGLE_WORKSPACE_CLI_TOKEN="$GOOGLE_GMAIL_TOKEN"
```

You can confirm the active account with `gws gmail users getProfile
--params '{"userId":"me"}'`.

### Send / reply / forward

```sh
# New message
gws gmail +send \
  --to alice@example.com \
  --cc team@example.com \
  --subject "Q1 status" \
  --body "Numbers attached."

# Reply (handles threadId, In-Reply-To, References automatically;
# To is the original sender, Subject gets the "Re: " prefix)
gws gmail +reply --message-id MSG_ID --body "Thanks — looks good."

# Reply-all
gws gmail +reply-all --message-id MSG_ID --body "+1"

# Forward to new recipients (preserves the original message body
# inline; original headers are summarised in the forward block)
gws gmail +forward --message-id MSG_ID --to bob@example.com
```

Each helper exits with a non-zero status and a JSON error on stderr if
Google rejects the request — surface that error verbatim. `+send` /
`+reply` need the `gmail.send` scope; if the user only granted
`gmail.readonly` you'll see `403 insufficientPermissions` and should ask
them to re-install the connector with the send box checked.

All the read / list / search / label / attachment recipes below are
intentionally **not** rewritten to `gws` — a one-line `curl ... | jq` is
shorter and easier to compose with shell pipelines.

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

## Write recipes

These all need `gmail.modify` (label / archive / trash) or
`gmail.send` (compose + send). If the user only granted
`gmail.readonly` at install you'll get `403 insufficientPermissions`
— surface that and ask them to re-install with the write boxes
checked.

### Mark a message read / unread, star it, archive it (gmail.modify)

```sh
MSG_ID='18f1a2b3c4d5e6f0'

# Mark as read = remove the UNREAD label
curl -sS -X POST -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"removeLabelIds":["UNREAD"]}' \
  "https://gmail.googleapis.com/gmail/v1/users/me/messages/$MSG_ID/modify"

# Star it = add the STARRED label
curl -sS -X POST -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"addLabelIds":["STARRED"]}' \
  "https://gmail.googleapis.com/gmail/v1/users/me/messages/$MSG_ID/modify"

# Archive = remove from INBOX (keeps in All Mail)
curl -sS -X POST -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"removeLabelIds":["INBOX"]}' \
  "https://gmail.googleapis.com/gmail/v1/users/me/messages/$MSG_ID/modify"
```

The `modify` endpoint takes `addLabelIds` and `removeLabelIds`
together — useful for atomic "archive + label" moves. Use the same
shape on `/threads/$THREAD_ID/modify` to apply across a whole thread.

### Apply a custom label

```sh
# 1. find or remember the label id from labels.list
LABEL_ID='Label_4'
MSG_ID='18f1a2b3c4d5e6f0'

curl -sS -X POST -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
  -H 'Content-Type: application/json' \
  --data "{\"addLabelIds\":[\"$LABEL_ID\"]}" \
  "https://gmail.googleapis.com/gmail/v1/users/me/messages/$MSG_ID/modify"
```

Creating a brand-new label needs the same scope:

```sh
curl -sS -X POST -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"name":"Follow up","messageListVisibility":"show","labelListVisibility":"labelShow"}' \
  "https://gmail.googleapis.com/gmail/v1/users/me/labels" \
  | jq '{id, name}'
```

### Trash a message or thread

```sh
MSG_ID='18f1a2b3c4d5e6f0'
curl -sS -X POST -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
  "https://gmail.googleapis.com/gmail/v1/users/me/messages/$MSG_ID/trash"

# Whole thread:
THREAD_ID='18f1a2b3c4d5e6f0'
curl -sS -X POST -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
  "https://gmail.googleapis.com/gmail/v1/users/me/threads/$THREAD_ID/trash"
```

Use `/untrash` (same shape) to restore. **Never** use
`messages.delete` — it permanently deletes and needs a higher scope
that we don't request.

### Send a brand-new email (gmail.send)

Gmail wants the message as a base64url-encoded RFC 2822 string.

```sh
# Compose the message
TO='alice@example.com'
SUBJECT='Quick hello'
BODY='Hi Alice,

Just a quick test note from the AceDataCloud Gmail connector.

Best,
Qingcai'

# Multi-line subject lines need MIME encoded-word for non-ASCII; ASCII is fine raw.
RAW=$(printf 'To: %s\r\nSubject: %s\r\nContent-Type: text/plain; charset=UTF-8\r\nMIME-Version: 1.0\r\n\r\n%s' \
  "$TO" "$SUBJECT" "$BODY" \
  | base64 | tr -d '\n' | tr '+/' '-_' | tr -d '=')

curl -sS -X POST -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
  -H 'Content-Type: application/json' \
  --data "{\"raw\":\"$RAW\"}" \
  "https://gmail.googleapis.com/gmail/v1/users/me/messages/send" \
  | jq '{id, threadId, labelIds}'
```

For non-ASCII subjects (Chinese / emoji), use MIME encoded-word:

```sh
SUBJECT_RAW='你好，季度复盘草稿'
SUBJECT_ENCODED="=?UTF-8?B?$(printf %s "$SUBJECT_RAW" | base64)?="
```

### Reply in-thread (keeps the thread together)

Reply by setting the `In-Reply-To` and `References` headers to the
Message-Id of the message you're replying to, **and** pass the
Gmail thread id in the API body:

```sh
ORIG_MSG_ID='18f1a2b3c4d5e6f0'
ORIG=$(curl -sS -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
  --get "https://gmail.googleapis.com/gmail/v1/users/me/messages/$ORIG_MSG_ID" \
  --data-urlencode 'format=metadata' \
  --data-urlencode 'metadataHeaders=Message-ID' \
  --data-urlencode 'metadataHeaders=Subject' \
  --data-urlencode 'metadataHeaders=From')
MID=$(echo "$ORIG" | jq -r '.payload.headers | from_entries | .["Message-ID"] // .["Message-Id"]')
FROM=$(echo "$ORIG" | jq -r '.payload.headers | from_entries | .From')
SUBJ=$(echo "$ORIG" | jq -r '.payload.headers | from_entries | .Subject')
TID=$(echo "$ORIG" | jq -r .threadId)

RAW=$(printf 'To: %s\r\nSubject: Re: %s\r\nIn-Reply-To: %s\r\nReferences: %s\r\nContent-Type: text/plain; charset=UTF-8\r\nMIME-Version: 1.0\r\n\r\n%s' \
  "$FROM" "$SUBJ" "$MID" "$MID" \
  'Replying inline — will follow up later today.' \
  | base64 | tr -d '\n' | tr '+/' '-_' | tr -d '=')

curl -sS -X POST -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
  -H 'Content-Type: application/json' \
  --data "{\"raw\":\"$RAW\",\"threadId\":\"$TID\"}" \
  "https://gmail.googleapis.com/gmail/v1/users/me/messages/send" \
  | jq '{id, threadId}'
```

Without the `threadId` in the body Gmail starts a brand-new thread
even with the right `In-Reply-To` headers.

### Save a draft instead of sending

Same `raw` payload, different endpoint — still costs `gmail.send`
(`drafts` shares the send scope under the hood for write):

```sh
curl -sS -X POST -H "Authorization: Bearer $GOOGLE_GMAIL_TOKEN" \
  -H 'Content-Type: application/json' \
  --data "{\"message\":{\"raw\":\"$RAW\"}}" \
  "https://gmail.googleapis.com/gmail/v1/users/me/drafts" \
  | jq '{id, message: {id: .message.id, threadId: .message.threadId}}'
```

## Common error codes

| HTTP | meaning | what to tell the user |
|---|---|---|
| `401 UNAUTHENTICATED` | token expired / revoked | "Reconnect the Gmail connector on the Connections page." |
| `403 insufficientPermissions` | scope missing | identify which scope (`gmail.modify` for label/archive/trash, `gmail.send` for sending) and suggest re-installing the connector with that box checked. |
| `403 userRateLimitExceeded` / `429` | quota / throttling | back off ~5s, then retry once. |
| `404 notFound` | wrong message / thread / attachment id | double-check the id, or fall back to `messages.list` with the right query. |
| `400 invalidQuery` | malformed `q` | print the `q` you sent + the error back to the user. |

Never log or echo `$GOOGLE_GMAIL_TOKEN` — treat it as a secret.
