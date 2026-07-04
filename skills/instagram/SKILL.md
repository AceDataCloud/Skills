---
name: instagram
description: Publish images, videos, Reels or carousels to your Instagram professional account via the Instagram Content Publishing API, and read your own recent media. Use when the user wants to post to Instagram (photo / video / reel / carousel), cross-post a visual, or review their own Instagram posts. Instagram is image/video-only (no text-only posts). Auth uses an access token (BYOC). 支持 Instagram 图片 / 视频 / Reels / 轮播发布。
when_to_use: |
  Trigger when the user wants to publish a photo, video, reel or carousel to
  their Instagram professional (Business/Creator) account, or review their own
  recent posts. Instagram only publishes image/video — there are no text-only
  posts. Publishing posts as their real account — confirm caption + media first.
connections: [instagram]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Call the **Instagram Graph API** (`graph.facebook.com`) with `curl + jq`. The
connector injects `$INSTAGRAM_ACCESS_TOKEN` (a token with
`instagram_content_publish` + `pages_read_engagement`; a Facebook Page token or
an Instagram-Login user token) and optionally `$INSTAGRAM_IG_USER_ID`. Never echo them.

Instagram publishes only **images / videos / reels** to a **professional**
(Business or Creator) account linked to a Facebook Page. There are no text-only posts.

### Resolve the Instagram account id

If `$INSTAGRAM_IG_USER_ID` is set, use it. Otherwise derive it from the token —
try the **Page-token** path first (`/me` is the Page), then fall back to the
**user-token** path (`/me/accounts` → linked Page → IG account), so either token
type the connector accepts resolves cleanly:

```bash
if [ -n "$INSTAGRAM_IG_USER_ID" ]; then
  IGID="$INSTAGRAM_IG_USER_ID"
else
  # Page access token: /me IS the Page, read its linked IG account directly
  IGID=$(curl -sS "https://graph.facebook.com/v21.0/me?fields=instagram_business_account&access_token=$INSTAGRAM_ACCESS_TOKEN" | jq -r '.instagram_business_account.id // empty')
  if [ -z "$IGID" ]; then
    # User access token: list the managed Page, then its linked IG account
    PAGE=$(curl -sS "https://graph.facebook.com/v21.0/me/accounts?access_token=$INSTAGRAM_ACCESS_TOKEN" | jq -r '.data[0].id // empty')
    IGID=$(curl -sS "https://graph.facebook.com/v21.0/$PAGE?fields=instagram_business_account&access_token=$INSTAGRAM_ACCESS_TOKEN" | jq -r '.instagram_business_account.id // empty')
  fi
fi
echo "ig_user_id=$IGID"
```

Errors are JSON with `error.message` / `error.code` — show them verbatim.
`401` / `OAuthException` → token expired or missing scope; a null `IGID` → the
token isn't linked to a professional IG account / Page (see Gotchas). Reconnect if needed.

## Publish a single image (two-step: create container → publish)

**Confirm the caption + image with the user first.** The `image_url` must be a
**public JPEG** URL (Instagram server-side cURLs it):

```bash
CID=$(curl -sS -X POST "https://graph.facebook.com/v21.0/$IGID/media" \
  -d "image_url=https://cdn.acedata.cloud/xxxx.jpg" \
  --data-urlencode "caption=One endpoint → posters, cards, mockups. #AI #API" \
  -d "access_token=$INSTAGRAM_ACCESS_TOKEN" | jq -r .id)
echo "container=$CID"

curl -sS -X POST "https://graph.facebook.com/v21.0/$IGID/media_publish" \
  -d "creation_id=$CID" -d "access_token=$INSTAGRAM_ACCESS_TOKEN" | jq .
# → {"id":"<IG_MEDIA_ID>"}
```

Get the permalink to hand back to the user:

```bash
curl -sS "https://graph.facebook.com/v21.0/<IG_MEDIA_ID>?fields=permalink&access_token=$INSTAGRAM_ACCESS_TOKEN" | jq -r .permalink
```

## Reels / video

Create with `media_type=REELS` + a public `video_url`, then **poll the container
status until FINISHED** before publishing (video processing takes time):

```bash
CID=$(curl -sS -X POST "https://graph.facebook.com/v21.0/$IGID/media" \
  -d "media_type=REELS" -d "video_url=https://cdn.acedata.cloud/xxxx.mp4" \
  --data-urlencode "caption=..." -d "access_token=$INSTAGRAM_ACCESS_TOKEN" | jq -r .id)

# poll until the video finishes processing (up to ~5 min) BEFORE publishing —
# publishing an IN_PROGRESS container is rejected:
for i in $(seq 1 60); do
  ST=$(curl -sS "https://graph.facebook.com/v21.0/$CID?fields=status_code&access_token=$INSTAGRAM_ACCESS_TOKEN" | jq -r .status_code)
  echo "status=$ST"; [ "$ST" = "FINISHED" ] && break
  [ "$ST" = "ERROR" ] || [ "$ST" = "EXPIRED" ] && { echo "container failed: $ST"; break; }
  sleep 5
done

curl -sS -X POST "https://graph.facebook.com/v21.0/$IGID/media_publish" \
  -d "creation_id=$CID" -d "access_token=$INSTAGRAM_ACCESS_TOKEN" | jq .
```

## Carousel (2–10 items)

Create each child with `is_carousel_item=true`, then a `media_type=CAROUSEL`
container with `children=<ID1>,<ID2>,...` + `caption`, then publish the carousel id.

## Gotchas

- **No text-only posts** — Instagram requires an image or video. Use a public
  **JPEG** for images (PNG/other formats are rejected; extended JPEG like MPO/JPS too).
- **Professional account required** — a Business/Creator IG account linked to a
  Facebook Page. If `instagram_business_account` is null, the account isn't a
  professional account or isn't linked; the user must fix that in IG / Page settings.
- **Media must be a public URL** on a server Instagram can reach; local files
  won't work. Host on cdn.acedata.cloud first.
- **Rate limit:** 100 API-published posts per 24h (a carousel counts as 1). Check
  via `GET /$IGID/content_publishing_limit`.
- **Page Publishing Authorization (PPA):** some Pages must complete PPA before API
  publishing works — surface the API error verbatim if it mentions PPA.
- API version: keep the `vXX.0` path current if you hit a version/deprecation error.

## Record the output

After you successfully publish and obtain the live permalink, call the built-in
`publish_artifact` tool ONCE so the user can track it in **My Outputs**:

```
publish_artifact(kind="image", channel="instagram", title="<title>", url="<the REAL permalink>", status="delivered")
```

Use the real returned URL — never fabricate one. Call it once per published item,
only after delivery is confirmed; skip it (or use `status="failed"`) if publishing failed.
See `_shared/artifacts.md`.
