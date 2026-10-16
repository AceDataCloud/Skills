---
name: tiktok
description: Publish a creator's video directly to TikTok after their review and confirmation, or upload it to drafts when requested.
when_to_use: |
  Trigger when the user wants to post a video to their own TikTok account
  or send it to TikTok drafts. For a direct post, show the TikTok publish
  card and use the creator's selected privacy and interaction settings.
  Use the inbox flow only when the user asks for a draft.
connections: [tiktok]
allowed_tools: [Bash, request_action_confirmation]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "2.4"
---

Call the **TikTok API v2** with `curl + jq`. The user's OAuth bearer token is in
`$TIKTOK_TOKEN`; every call needs `Authorization: Bearer $TIKTOK_TOKEN`. Base
URL: `https://open.tiktokapis.com/v2`.

```bash
T="https://open.tiktokapis.com/v2"; AUTH="Authorization: Bearer $TIKTOK_TOKEN"
```

Responses wrap everything in `{"data":…,"error":{"code","message","log_id"}}`.
**Check `error.code`, not just the HTTP status** — several real failures
(`spam_risk_too_many_posts`, `spam_risk_user_banned_from_posting`,
`reached_active_user_cap`) come back as **HTTP 200** with a non-`ok` code. Show
`error.message` verbatim. `401` / `access_token_invalid` = re-connect TikTok.

## Read the account

```bash
# Basic profile — open_id identifies the user for every posting call
curl -sS -H "$AUTH" "$T/user/info/?fields=open_id,display_name,avatar_url" \
  | jq '.data.user'
```

Follower / like counts, bio, and the user's video list need the **Display API**
scopes (`user.info.stats`, `user.info.profile`, `video.list`), which this app
has not been granted — don't call `/v2/video/list/` or request those fields,
they will fail with `scope_not_authorized`.

## Direct Post to the creator's profile

The production app has passed TikTok's Content Posting API audit. A direct post
publishes to the creator's profile after processing; it is not a draft. Never
choose a privacy level, interaction setting, or disclosure on the creator's
behalf. Never retry an init request while its `publish_id` is processing.

Required sequence:

1. Identify the exact video and its source. Measure its duration and preview
   it. A server-hosted video must use a public, non-redirecting HTTPS URL under
   the verified `acedata.cloud` domain (`PULL_FROM_URL`). A creator-selected
   device-local MP4 may use `FILE_UPLOAD` and must be no larger than 64 MB.
2. Query the selected connection with
   `python3 skills/tiktok/scripts/tiktok.py creator-info`. Check
   `creator_username` against the account the creator named. Copy the current
   nickname, avatar, `privacy_level_options`, interaction restrictions, and
   maximum duration into `request_action_confirmation` with
   `kind: "tiktok.publish"` and the real video preview. Do not invent or
   preselect a privacy option.
3. If cancelled, stop. If confirmed, use exactly the card's returned `title`,
   `privacy_level`, `disable_comment`, `disable_duet`, `disable_stitch`,
   `brand_organic_toggle`, and `brand_content_toggle`. Add `is_aigc: true`
   for AI-generated content and `false` otherwise. For an Ace Data Cloud brand
   promotion, the creator must select the own-brand promotional disclosure.
   Store these values in a temporary JSON file outside the repository.
4. Submit **once** after confirmation, with the exact selected account:

   ```bash
   # Server-hosted video on the verified domain:
   python3 skills/tiktok/scripts/tiktok.py post-url "$VIDEO_URL" \
     --duration-sec "$DURATION" \
     --expected-creator-username "$CONFIRMED_CREATOR_USERNAME" \
     --values-file "$VALUES_JSON" --confirmed

   # Creator-selected device-local MP4:
   python3 skills/tiktok/scripts/tiktok.py post-file video.mp4 \
     --duration-sec "$DURATION" \
     --expected-creator-username "$CONFIRMED_CREATOR_USERNAME" \
     --values-file "$VALUES_JSON" --confirmed
   ```

   Both commands re-query creator info and reject a different account, an
   unavailable privacy level, disabled interactions, or an overlong video.
   Never substitute confirmed fields after this check.
5. Poll the returned `publish_id` with `status` until `PUBLISH_COMPLETE` or a
   terminal failure. Report the actual outcome. An accepted init or successful
   file transfer is not a published post.

## Upload the video to the user's drafts

Use this when the creator explicitly asks for a draft. The video lands in their TikTok **inbox /
drafts**; they open the TikTok app to add caption, sound and privacy, then post.

Required order:

1. Identify the exact video and its source: a creator's device-local file or a
   server-hosted URL under the verified `acedata.cloud` domain. Preview it.
2. Call `request_action_confirmation` with `kind: "generic"`, the real video
   preview, and a summary that says this uploads to drafts rather than publishing.
3. If cancelled, stop. If confirmed, run exactly one upload. For a device-local
   file use `python3 skills/tiktok/scripts/tiktok.py upload video.mp4`. For a
   server-hosted video use
   `python3 skills/tiktok/scripts/tiktok.py upload-url "$VIDEO_URL"`.
4. Poll with `python3 skills/tiktok/scripts/tiktok.py status PUBLISH_ID` until
   terminal. Never call `upload` again while polling.

Two source modes are available. The developer portal verified `acedata.cloud`
on 2026-10-03, covering its subdomains. Server-hosted videos on that domain
must use `PULL_FROM_URL`; use `FILE_UPLOAD` only for a creator's device-local
file. Verify that the exact URL is public HTTPS and does not redirect.

### FILE_UPLOAD (creator device-local file)

Use this only for a file the creator selected from their own device. Files
under 64 MB go up as a single chunk.

```bash
SIZE=$(stat -f%z video.mp4 2>/dev/null || stat -c%s video.mp4)

INIT=$(curl -sS -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d "$(jq -n --argjson s "$SIZE" \
    '{source_info:{source:"FILE_UPLOAD", video_size:$s, chunk_size:$s, total_chunk_count:1}}')" \
  "$T/post/publish/inbox/video/init/")
echo "$INIT" | jq '{publish_id:.data.publish_id, error:.error.code}'

UPLOAD_URL=$(echo "$INIT" | jq -r '.data.upload_url')
curl -sS -X PUT "$UPLOAD_URL" \
  -H "Content-Type: video/mp4" \
  -H "Content-Length: $SIZE" \
  -H "Content-Range: bytes 0-$((SIZE-1))/$SIZE" \
  --data-binary @video.mp4 -o /dev/null -w '%{http_code}\n'
```

The `PUT` returns **201** when the whole file landed (206 for intermediate
chunks). `upload_url` expires in **1 hour**.

### PULL_FROM_URL (only from a verified domain)

```bash
python3 skills/tiktok/scripts/tiktok.py upload-url "$VIDEO_URL"
```

The helper requires public HTTPS under the verified `acedata.cloud` domain,
`video/mp4`, and no redirects. Domain verification covers subdomains downward.

## Poll status

```bash
curl -sS -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d "$(jq -n --arg id "$PUBLISH_ID" '{publish_id:$id}')" \
  "$T/post/publish/status/fetch/" | jq '.data | {status, fail_reason}'
```

`PROCESSING_UPLOAD` / `PROCESSING_DOWNLOAD` → **`SEND_TO_USER_INBOX`** = done,
the video is waiting in the creator's TikTok inbox. Tell them to open the
TikTok app to finish posting, and that processing takes a few minutes.

Don't retry on `auth_removed`, `spam_risk_text`, `spam_risk`, or
`spam_risk_user_banned_from_posting` — those are terminal. `internal` is
retryable.

## Gotchas

- **Never preselect `privacy_level`** in the confirmation card. The helper
  checks the creator's selection against fresh `privacy_level_options` before
  making the one Direct Post call. Branded content cannot be `SELF_ONLY`.
- Connections made with the former Sandbox app must be reconnected to the
  Production app. If TikTok returns
  `unaudited_client_can_only_post_to_private_accounts`, stop and ask the
  creator to reconnect; do not retry the same post or change its privacy.
- Rate limits per user token: `creator_info/query` 20/min, `video/init/`
  **6/min**, `status/fetch/` 30/min. TikTok also caps posts at roughly 15/day
  per creator, **shared across all apps** — another app can exhaust it.
- `SEND_TO_USER_INBOX` is success for this flow, not an intermediate state.
  Don't wait for `PUBLISH_COMPLETE` — that only happens once the user posts
  from the app.
