---
name: mastodon
description: Publish, delete and read your own posts (toots) on any Mastodon instance via the Mastodon REST API. Use when the user wants to post a toot to their Mastodon / fediverse account, cross-post an article as a short dev-focused post, delete a toot, or list their own recent posts with engagement stats (boosts, favourites, replies).
when_to_use: |
  Trigger when the user wants to publish a status/toot to their Mastodon
  account, delete one, or review their own recent posts and engagement.
  Mastodon is federated: the connector stores the instance base URL plus a
  personal access token, so every call targets the user's own instance.
  Confirm visibility (public/unlisted) before posting publicly.
connections: [mastodon]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Call the **Mastodon REST API** with `curl + jq`. Two connector credentials are
injected: `$MASTODON_BASE_URL` (the instance, e.g. `https://mastodon.social`)
and `$MASTODON_ACCESS_TOKEN`. Every request sends the header
`Authorization: Bearer $MASTODON_ACCESS_TOKEN`.

Errors come back as JSON `{"error":"<message>"}` — show it verbatim. `401`
(`"The access token is invalid"`) means the token is wrong/revoked → the user
must re-connect the Mastodon connector. Posting needs the token to have the
`write` (or `write:statuses`) scope.

**Always confirm the token + account first** (also gives the account `id` you
need to list your own toots):

```bash
curl -sS "$MASTODON_BASE_URL/api/v1/accounts/verify_credentials" \
  -H "Authorization: Bearer $MASTODON_ACCESS_TOKEN" \
  | jq '{id, username, acct, display_name, followers: .followers_count, statuses: .statuses_count}'
```

## Post a toot

**Confirm with the user before posting publicly.** Default `visibility` to
`unlisted` unless they say post publicly; use `public` only on request.

```bash
STATUS_TEXT="Hello fediverse 👋 #introductions"
curl -sS -X POST "$MASTODON_BASE_URL/api/v1/statuses" \
  -H "Authorization: Bearer $MASTODON_ACCESS_TOKEN" \
  -H "Idempotency-Key: $(uuidgen)" \
  --data-urlencode "status=$STATUS_TEXT" \
  --data-urlencode "visibility=unlisted" \
  --data-urlencode "language=en" \
  | jq '{id, url, visibility, created_at}'
```

- `visibility` is one of `public`, `unlisted`, `private`, `direct`.
- Optional params: `spoiler_text` (content warning), `in_reply_to_id` (reply),
  `sensitive=true`, `language` (ISO 639-1).
- `Idempotency-Key` (any unique string; `uuidgen` here) prevents duplicate
  posts if the request is retried within ~1h. Use `--data-urlencode` so
  hashtags, emoji and newlines in the text are encoded correctly.
- Default post length is 500 chars (instance-configurable); longer text →
  `422 {"error":"Validation failed: Text ..."}`.

## List my recent toots + engagement

Use the `id` from `verify_credentials`:

```bash
ACCT_ID="14715"   # from verify_credentials
curl -sS "$MASTODON_BASE_URL/api/v1/accounts/$ACCT_ID/statuses?limit=20&exclude_replies=true&exclude_reblogs=true" \
  -H "Authorization: Bearer $MASTODON_ACCESS_TOKEN" \
  | jq '.[] | {id, url, boosts: .reblogs_count, favs: .favourites_count, replies: .replies_count, created_at}'
```

`limit` max 40. Other filters: `only_media`, `pinned`, `tagged=<hashtag>`.

## Delete a toot

```bash
curl -sS -X DELETE "$MASTODON_BASE_URL/api/v1/statuses/STATUS_ID" \
  -H "Authorization: Bearer $MASTODON_ACCESS_TOKEN" | jq '{id, deleted: true}'
```

Deleting returns the status with its source `text` so you can delete-and-redraft.
`404 {"error":"Record not found"}` = not yours or already gone.

## Attaching media (optional)

Upload each image/video via `POST $MASTODON_BASE_URL/api/v2/media`
(`multipart/form-data`, field `file`) to get a media id, then pass the ids as
`media_ids[]` when posting the status. See the docs for the full media contract:
https://docs.joinmastodon.org/methods/media/

## Gotchas

- **Federated:** the API only ever targets `$MASTODON_BASE_URL` (the user's own
  instance). There is no global endpoint — a token from instance A won't work
  on instance B.
- **Scopes:** reading needs `read` (or `read:accounts`/`read:statuses`);
  posting/deleting needs `write` (or `write:statuses`). A `403`
  (`"This action is outside the authorized scopes"`) means the token lacks a scope.
- **Rate limits:** Mastodon rate-limits per token; space out bulk posts or you'll
  get `429`.
- `verify_credentials` returns HTML in fields like `note`; the plaintext source
  lives under the `source` object.


## Record the output

After you successfully publish and obtain the live result URL, call the built-in
`publish_artifact` tool ONCE so the user can track this deliverable in **My Outputs**:

```
publish_artifact(kind="message", channel="mastodon", title="<title>", url="<the REAL returned URL>", status="delivered")
```

Use the real returned URL — never fabricate one. Call it once per published item,
only after delivery is confirmed; skip it (or use `status="failed"`) if publishing failed.
See `_shared/artifacts.md`.
