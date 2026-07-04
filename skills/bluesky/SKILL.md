---
name: bluesky
description: Publish (with optional images), delete and read your own posts on Bluesky via the AT Protocol (XRPC). Use when the user wants to post to their Bluesky account (text or 带图 / with a picture), cross-post an article as a short dev-focused post, attach an image, delete a post, or list their own recent posts with engagement stats (reposts, likes, replies). Auth uses the user's handle plus an App Password.
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
  version: "1.1"
---

Everything runs through the shipped CLI [`scripts/bluesky.py`](scripts/bluesky.py)
— self-contained (`requests` + `Pillow`, both preinstalled in the sandbox). One
call creates the session, auto-computes clickable **facets** (links, #hashtags,
@mentions with correct UTF-8 byte offsets), and for image posts downloads the
file, **resizes/recompresses it to Bluesky's ~1 MB blob limit**, `uploadBlob`s it
and builds the `app.bsky.embed.images` embed — so there's no fragile
`curl + jq + heredoc` to hand-assemble (the old inline recipe kept breaking on
shell quoting, especially once an image + facets were involved).

Three connector credentials are injected: `$BLUESKY_HANDLE`
(e.g. `name.bsky.social`), `$BLUESKY_APP_PASSWORD` (an App Password from Bluesky
**Settings → Privacy and Security → App Passwords**, NOT the login password) and
`$BLUESKY_SERVICE` (PDS base URL, default `https://bsky.social`). The CLI reads
them from the env — never echo them.

```sh
BSKY="$SKILL_DIR/scripts/bluesky.py"
python3 "$BSKY" whoami          # verify the session → {did, handle, service}
```

If `whoami` fails with `session_failed` / `AuthenticationRequired`, the
identifier or App Password is wrong. The **#1 cause is a bare handle** — the CLI
auto-appends `.bsky.social` to a bare username on the default PDS, but if it
still fails the user must reconnect the connector with their **full** handle
(`name.bsky.social`, a custom domain, a DID, or the account email) and a valid
App Password.

## Post — text, images and links in one call

**Confirm the text with the user before posting** (it publishes as their real
account). Text ≤ **300 graphemes**. Clickable links / #hashtags / @mentions are
turned into facets automatically — just write them in the text, no byte-offset
math needed.

```sh
# plain text post
python3 "$BSKY" post --text "Hello Bluesky 👋 shipping with the AT Protocol"

# 带图发送 / post WITH an image (URL or local path) — the image is downloaded,
# resized to fit the blob limit, uploaded and embedded automatically:
python3 "$BSKY" post \
  --text "Stop wiring 3 image APIs. One endpoint → posters, cards, mockups. https://platform.acedata.cloud/documents/openai-images-generations-integration #AI #API" \
  --image "https://cdn.acedata.cloud/xxxx.png" --alt "AI image API hero"

# up to 4 images, each with its own --alt (paired by order)
python3 "$BSKY" post --text "gallery" --image a.png --alt "one" --image b.png --alt "two"
```

Multi-line text or lots of emoji? Skip shell-quoting headaches by writing the
text to a file and using `--text-file` (or pipe via `--text -`):

```sh
cat > /tmp/post.txt <<'EOF'
Line one 🎨

Line two with a link https://platform.acedata.cloud #AI
EOF
python3 "$BSKY" post --text-file /tmp/post.txt --image "https://cdn.acedata.cloud/xxxx.png"
```

Success prints
`{"posted":true,"uri":"at://…","url":"https://bsky.app/profile/<handle>/post/<rkey>", ...}`.
The `url` is the public, shareable link — hand it to the user verbatim.

## List my recent posts + engagement

```sh
python3 "$BSKY" list --limit 20                    # default filter: posts_no_replies
python3 "$BSKY" list --limit 50 --filter posts_with_media
```

`--filter`: `posts_no_replies` | `posts_with_replies` | `posts_with_media` |
`posts_and_author_threads`. `--limit` max 100.

## Delete a post

```sh
python3 "$BSKY" delete --uri "at://did:plc:xxxx/app.bsky.feed.post/3kabc123xyz"
```

Pass the full `at://…` post `uri` (from `list` or a prior `post`); the CLI
extracts the `rkey`. An empty result / `deleted:true` is success.

## Gotchas

- **App Password, not account password:** creating a session with the real
  login password may be rejected or trip 2FA. Always the App Password from
  Settings → App Passwords.
- **Facets & image resizing are automatic** — the CLI computes link/#tag/@mention
  byte offsets and shrinks oversized images to the ~1 MB blob limit for you.
- **300 graphemes**, counted as user-perceived characters (emoji = 1).
- **Rate limits:** the PDS rate-limits writes per account; space out bulk posts
  or you'll get `429 {"error":"RateLimitExceeded"}`.
- **Self-hosted PDS:** if the user runs their own PDS, `$BLUESKY_SERVICE` points
  there; all XRPC calls target that host, not `bsky.social`.
- The CLI creates a fresh short-lived session on **every** invocation, so an
  expiring `accessJwt` is never a concern — just run the command again.


## Record the output

After you successfully publish and obtain the live result URL, call the built-in
`publish_artifact` tool ONCE so the user can track this deliverable in **My Outputs**:

```
publish_artifact(kind="message", channel="bluesky", title="<title>", url="<the REAL returned URL>", status="delivered")
```

Use the real returned URL — never fabricate one. Call it once per published item,
only after delivery is confirmed; skip it (or use `status="failed"`) if publishing failed.
See `_shared/artifacts.md`.
