---
name: bluesky
description: Publish, delete and read your own posts on Bluesky via the AT Protocol (XRPC). Use when the user wants to post to their Bluesky account, cross-post an article as a short dev-focused post, delete a post, or list their own recent posts with engagement stats (reposts, likes, replies). Auth uses the user's handle plus an App Password.
when_to_use: |
  Trigger when the user wants to publish a post to their Bluesky account,
  delete one, or review their own recent posts and engagement. Bluesky runs on
  the AT Protocol: the connector stores the user's handle plus an App Password
  (NOT the main account password) and a PDS service URL (default
  https://bsky.social). Confirm the post text with the user before publishing.
connections: [bluesky]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Call the **Bluesky AT Protocol** XRPC endpoints with `curl + jq`. Three
connector credentials are injected: `$BLUESKY_HANDLE` (e.g. `name.bsky.social`),
`$BLUESKY_APP_PASSWORD` (an App Password created in Bluesky **Settings →
Privacy and Security → App Passwords**, NOT the account login password) and
`$BLUESKY_SERVICE` (the PDS base URL, default `https://bsky.social`).

Errors come back as JSON `{"error":"<name>","message":"<detail>"}` — show it
verbatim. A `401 {"error":"AuthenticationRequired","message":"Invalid identifier
or password"}` on session creation means the identifier or App Password is
wrong/revoked. The **#1 cause is a bare handle**: the identifier must be the
FULL handle (`alice.bsky.social`), a DID, or the account email — a bare
`alice` will NOT resolve. Step 1 auto-appends `.bsky.social` to a bare handle
on the default PDS; if it still fails, the user must re-connect the Bluesky
connector with the full handle (or generate a fresh App Password).

## Step 1 — always create a session first

Everything needs a short-lived `accessJwt` and your account `did`. Do this once
per task and reuse the values. The identifier must be a full handle, DID or
email — normalize a bare username (no `.` / `@`) to `<name>.bsky.social` when
using the default PDS, otherwise `createSession` returns `AuthenticationRequired`:

```bash
SVC="${BLUESKY_SERVICE:-https://bsky.social}"
ID="$BLUESKY_HANDLE"
# Bare username → full handle on the default bsky.social PDS. A dotted handle
# (custom domain), a DID (`did:...`) or an email are already valid — leave them.
case "$ID" in
  *.* | *@* | did:*) : ;;
  *) [ "$SVC" = "https://bsky.social" ] && ID="$ID.bsky.social" ;;
esac
SESSION=$(curl -sS -X POST "$SVC/xrpc/com.atproto.server.createSession" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg id "$ID" --arg pw "$BLUESKY_APP_PASSWORD" \
        '{identifier:$id, password:$pw}')")
echo "$SESSION" | jq '{did, handle, active}'
JWT=$(echo "$SESSION" | jq -r .accessJwt)
DID=$(echo "$SESSION" | jq -r .did)
```

If `JWT` / `DID` are empty or `null`, print the raw `$SESSION` (it contains the
error) and stop — do not continue to post. On `AuthenticationRequired`, tell the
user to reconnect the connector using their **full** handle (e.g.
`name.bsky.social`, not `name`) and a valid App Password.

## Post to Bluesky

**Confirm the text with the user before posting.** Text is limited to **300
graphemes**; longer text → `400 {"error":"InvalidRequest"}`. `createdAt` must be
an ISO-8601 UTC timestamp.

```bash
TEXT="Hello Bluesky 👋 shipping with the AT Protocol"
NOW=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)
curl -sS -X POST "$SVC/xrpc/com.atproto.repo.createRecord" \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg did "$DID" --arg text "$TEXT" --arg now "$NOW" \
        '{repo:$did, collection:"app.bsky.feed.post",
          record:{ "$type":"app.bsky.feed.post", text:$text, createdAt:$now, langs:["en"] }}')" \
  | jq '{uri, cid}'
```

The returned `uri` looks like `at://did:plc:xxxx/app.bsky.feed.post/<rkey>`. The
public web URL is `https://bsky.app/profile/$ID/post/<rkey>` where `$ID` is the
normalized handle from Step 1 (or use the `did`) and `<rkey>` is the last path
segment of the `uri`.

### Clickable links, mentions and hashtags (facets)

Plain URLs/hashtags in `text` are shown but **not clickable** — Bluesky needs
`facets` with UTF-8 **byte** offsets. Add a hashtag link like this (byteStart/
byteEnd are byte indices into the UTF-8 text, not character indices):

```bash
# text = "New post about #ai" — "#ai" starts at byte 15, ends at byte 18
curl -sS -X POST "$SVC/xrpc/com.atproto.repo.createRecord" \
  -H "Authorization: Bearer $JWT" -H "Content-Type: application/json" \
  -d "$(jq -n --arg did "$DID" --arg now "$NOW" '
    {repo:$did, collection:"app.bsky.feed.post",
     record:{ "$type":"app.bsky.feed.post", text:"New post about #ai", createdAt:$now,
       facets:[ { index:{byteStart:15, byteEnd:18},
                  features:[{ "$type":"app.bsky.richtext.facet#tag", tag:"ai" }] } ] }}')" \
  | jq '{uri, cid}'
```

For a link, use feature `app.bsky.richtext.facet#link` with a `uri` field; for a
mention, `app.bsky.richtext.facet#mention` with a `did`. Compute byte offsets
with e.g. `printf '%s' "$prefix" | wc -c`.

## List my recent posts + engagement

```bash
curl -sS "$SVC/xrpc/app.bsky.feed.getAuthorFeed?actor=$DID&limit=20&filter=posts_no_replies" \
  -H "Authorization: Bearer $JWT" \
  | jq '.feed[] | {uri: .post.uri,
                   text: .post.record.text,
                   reposts: .post.repostCount,
                   likes: .post.likeCount,
                   replies: .post.replyCount,
                   at: .post.indexedAt}'
```

`limit` max 100. `filter` options: `posts_with_replies`, `posts_no_replies`,
`posts_with_media`, `posts_and_author_threads`.

## Delete a post

`deleteRecord` needs the `rkey` (the last path segment of the post `uri`):

```bash
POST_URI="at://$DID/app.bsky.feed.post/3kabc123xyz"
RKEY="${POST_URI##*/}"
curl -sS -X POST "$SVC/xrpc/com.atproto.repo.deleteRecord" \
  -H "Authorization: Bearer $JWT" -H "Content-Type: application/json" \
  -d "$(jq -n --arg did "$DID" --arg rkey "$RKEY" \
        '{repo:$did, collection:"app.bsky.feed.post", rkey:$rkey}')" \
  | jq '{deleted: true, rkey: "'"$RKEY"'"}'
```

An empty `{}` response is success. `400 {"error":"InvalidRequest"}` usually
means the record is already gone or the `rkey` is wrong.

## Attaching images (optional)

Upload each image via `POST $SVC/xrpc/com.atproto.repo.uploadBlob`
(`Content-Type: image/jpeg`, raw bytes body, Bearer `$JWT`) → returns a `blob`
object. Then set `record.embed` to
`{ "$type":"app.bsky.embed.images", images:[{ alt:"<desc>", image:<blob> }] }`.
Max 4 images per post; each blob ≲ 1 MB (resize/compress first).

## Gotchas

- **App Password, not account password:** creating a session with the real
  login password may be rejected or trip 2FA. Always the App Password from
  Settings → App Passwords.
- **Byte offsets, not char offsets:** facet `byteStart`/`byteEnd` are UTF-8
  byte indices — emoji and CJK take multiple bytes. Get them wrong and the
  link highlights the wrong span.
- **300 graphemes**, counted as user-perceived characters (emoji = 1).
- **Rate limits:** the PDS rate-limits writes per account; space out bulk posts
  or you'll get `429 {"error":"RateLimitExceeded"}`.
- **Self-hosted PDS:** if the user runs their own PDS, `$BLUESKY_SERVICE` points
  there; all XRPC calls target that host, not `bsky.social`.
- The `accessJwt` is short-lived (~2h). For a single task it's fine; if it
  expires mid-task, just re-run Step 1.
