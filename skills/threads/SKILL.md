---
name: threads
description: Publish text, image, video or carousel posts to your Threads (@threads) account via the official Threads API, and read your own recent posts. Use when the user wants to post to Threads, cross-post a short update / thread, attach an image or link, or review their own Threads posts. Auth uses a Threads access token (BYOC). 支持 Threads 文本 / 图片 / 视频 / 轮播发布与自有贴文读取。
when_to_use: |
  Trigger when the user wants to publish a post to their Threads account or
  review their own recent Threads posts. Threads is Meta's text-first social
  app; the connector stores a Threads access token with threads_content_publish.
  Posting publishes as their real account — confirm the text with the user first.
connections: [threads]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Call the **Threads API** (`graph.threads.net`) with `curl + jq`. The connector
injects one credential: `$THREADS_ACCESS_TOKEN` (a long-lived Threads access
token with the `threads_basic` + `threads_content_publish` scopes). Never echo it.

Resolve the caller's Threads user id once (every publish needs it):

```bash
ME=$(curl -sS "https://graph.threads.net/v1.0/me?fields=id,username&access_token=$THREADS_ACCESS_TOKEN")
TID=$(echo "$ME" | jq -r .id)
echo "$ME"     # {"id":"<THREADS_USER_ID>","username":"..."}
```

Errors are JSON with `error.message` / `error.code` — show them verbatim.
`401` / `OAuthException` → the token expired or lacks scope; reconnect the
Threads connector.

## Publish a post (two-step: create container → publish)

**Confirm the text with the user first** (it publishes as their real account).
Text ≤ **500 characters** (emoji counted as UTF-8 bytes).

Step 1 — create a media container. Text-only (guard the 500-byte limit first):

```bash
TEXT="Shipping one API for AI images → posters, cards, mockups. https://platform.acedata.cloud #AI #API"
[ "$(printf %s "$TEXT" | wc -c)" -le 500 ] || { echo "text exceeds Threads 500-byte limit — shorten it"; }
CID=$(curl -sS -X POST "https://graph.threads.net/v1.0/$TID/threads" \
  --data-urlencode "media_type=TEXT" \
  --data-urlencode "text=$TEXT" \
  -d "access_token=$THREADS_ACCESS_TOKEN" | jq -r .id)
echo "container=$CID"
```

Image post — add `media_type=IMAGE` + a **public** `image_url` (Threads cURLs it
server-side, so it must be on a public server); video uses `media_type=VIDEO` + `video_url`:

```bash
CID=$(curl -sS -X POST "https://graph.threads.net/v1.0/$TID/threads" \
  --data-urlencode "media_type=IMAGE" \
  -d "image_url=https://cdn.acedata.cloud/xxxx.jpg" \
  --data-urlencode "text=caption here" \
  -d "access_token=$THREADS_ACCESS_TOKEN" | jq -r .id)
```

Step 2 — publish the container. **Text posts publish immediately; for IMAGE /
VIDEO / carousel containers you MUST wait ≥30s first** so Threads can
fetch/process the upload — publishing too early fails or returns no id:

```bash
sleep 30   # REQUIRED for IMAGE / VIDEO / carousel; skip for TEXT-only posts
curl -sS -X POST "https://graph.threads.net/v1.0/$TID/threads_publish" \
  -d "creation_id=$CID" -d "access_token=$THREADS_ACCESS_TOKEN" | jq .
# → {"id":"<THREADS_MEDIA_ID>"}
```

If `threads_publish` returns no id, the container isn't ready yet — poll
`GET /v1.0/<CID>?fields=status&access_token=$THREADS_ACCESS_TOKEN` until
`status=FINISHED`, then retry publish.

Get the public URL of the published post and hand it to the user:

```bash
curl -sS "https://graph.threads.net/v1.0/<THREADS_MEDIA_ID>?fields=id,permalink&access_token=$THREADS_ACCESS_TOKEN" | jq -r .permalink
```

## Carousel (2–20 items)

Create each child with `is_carousel_item=true`, then a `media_type=CAROUSEL`
container with `children=<ID1>,<ID2>,...`, then publish the carousel id. Links:
add `link_attachment=<URL>` (text-only posts, ≤5 links). Topic tag: `topic_tag=<TAG>`.

## List my recent posts

```bash
curl -sS "https://graph.threads.net/v1.0/$TID/threads?fields=id,text,permalink,timestamp&limit=20&access_token=$THREADS_ACCESS_TOKEN" | jq '.data'
```

## Gotchas

- **500-char limit**; emoji count as their UTF-8 byte length.
- **Media must be a public URL** — Threads server-side cURLs `image_url`/`video_url`;
  local files won't work. Upload to a public host / cdn.acedata.cloud first.
- **Wait ~30s before publishing media** containers (text publishes instantly); if
  `threads_publish` doesn't return an id, poll `GET /<container-id>?fields=status`.
- **Rate limit:** 250 published posts per 24h per profile (a carousel counts as 1).
- Threads tokens differ from Facebook/Instagram tokens — they come from the
  Threads OAuth flow on `graph.threads.net`, not `graph.facebook.com`.

## Record the output

After you successfully publish and obtain the live permalink, call the built-in
`publish_artifact` tool ONCE so the user can track it in **My Outputs**:

```
publish_artifact(kind="message", channel="threads", title="<title>", url="<the REAL permalink>", status="delivered")
```

Use the real returned URL — never fabricate one. Call it once per published item,
only after delivery is confirmed; skip it (or use `status="failed"`) if publishing failed.
See `_shared/artifacts.md`.
