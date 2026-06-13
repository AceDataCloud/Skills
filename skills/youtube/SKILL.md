---
name: youtube
description: Search YouTube, read your own channel and uploaded videos (stats, comments), and upload new videos via the YouTube Data API v3. Use when the user mentions YouTube, "my channel", "my videos", searching YouTube, video views / likes / stats, uploading a video to YouTube, or checking how a published video is doing.
when_to_use: |
  Trigger when the user wants to search YouTube, inspect their own
  channel / uploaded videos (views, likes, comments), look up a
  video's stats, or upload a new video to their channel. The
  installed connector always grants `youtube.readonly` (search + read
  your channel and videos); the user opts in to `youtube.upload` at
  install time to publish videos — confirm before uploading and
  re-prompt to re-install if the upload scope is missing.
connections: [google/youtube]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Call the **YouTube Data API v3** with `curl + jq`. The user's OAuth bearer
token is in `$GOOGLE_YOUTUBE_TOKEN`; every call needs it as
`Authorization: Bearer $GOOGLE_YOUTUBE_TOKEN`. Base URL:
`https://www.googleapis.com/youtube/v3`.

The token always carries `youtube.readonly` plus identity scopes
(`openid email profile`); if the user opted in at install it also
carries `youtube.upload` (publish videos).

Responses are standard JSON; failures surface as
`{"error": {"code": 401|403|..., "message": "..."}}` — show that error
verbatim. `401` → token expired, the user must re-connect the YouTube
connector. `403 insufficientPermissions` on an upload → the user did
not grant `youtube.upload`; ask them to re-connect with the upload box
checked.

**Always start with the channel check** to confirm the connection works
and learn which channel you're operating against.

```bash
curl -sS -H "Authorization: Bearer $GOOGLE_YOUTUBE_TOKEN" \
  "https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics,contentDetails&mine=true" \
  | jq '.items[0] | {title: .snippet.title, subs: .statistics.subscriberCount, views: .statistics.viewCount, uploads: .contentDetails.relatedPlaylists.uploads}'
```

## Search YouTube

```bash
# Public search (any video). type can be video|channel|playlist.
curl -sS -H "Authorization: Bearer $GOOGLE_YOUTUBE_TOKEN" \
  --data-urlencode "q=ai video automation" \
  --data-urlencode "part=snippet" \
  --data-urlencode "type=video" \
  --data-urlencode "maxResults=10" \
  -G "https://www.googleapis.com/youtube/v3/search" \
  | jq '.items[] | {videoId: .id.videoId, title: .snippet.title, channel: .snippet.channelTitle, published: .snippet.publishedAt}'
```

Add `--data-urlencode "order=date|viewCount|rating|relevance"` to sort,
or `--data-urlencode "publishedAfter=2026-01-01T00:00:00Z"` to window.

## See my uploaded videos

YouTube has no "list my videos" call directly — read the channel's
**uploads playlist**, then page its items.

```bash
# 1. Get the uploads playlist id (UU... ) — same as channels call above.
UPLOADS=$(curl -sS -H "Authorization: Bearer $GOOGLE_YOUTUBE_TOKEN" \
  "https://www.googleapis.com/youtube/v3/channels?part=contentDetails&mine=true" \
  | jq -r '.items[0].contentDetails.relatedPlaylists.uploads')

# 2. List recent uploads (50/page; follow .nextPageToken for more).
curl -sS -H "Authorization: Bearer $GOOGLE_YOUTUBE_TOKEN" \
  -G "https://www.googleapis.com/youtube/v3/playlistItems" \
  --data-urlencode "part=snippet,contentDetails" \
  --data-urlencode "playlistId=$UPLOADS" \
  --data-urlencode "maxResults=50" \
  | jq '.items[] | {videoId: .contentDetails.videoId, title: .snippet.title, published: .snippet.publishedAt}'
```

Paginate by passing `--data-urlencode "pageToken=$PAGE_TOKEN"` with the
`.nextPageToken` from the previous response.

## Video stats (views / likes / comments)

```bash
# Accepts a comma-separated id list.
curl -sS -H "Authorization: Bearer $GOOGLE_YOUTUBE_TOKEN" \
  -G "https://www.googleapis.com/youtube/v3/videos" \
  --data-urlencode "part=snippet,statistics,status" \
  --data-urlencode "id=VIDEO_ID_1,VIDEO_ID_2" \
  | jq '.items[] | {title: .snippet.title, views: .statistics.viewCount, likes: .statistics.likeCount, comments: .statistics.commentCount, privacy: .status.privacyStatus}'
```

## Read comments on a video

```bash
curl -sS -H "Authorization: Bearer $GOOGLE_YOUTUBE_TOKEN" \
  -G "https://www.googleapis.com/youtube/v3/commentThreads" \
  --data-urlencode "part=snippet" \
  --data-urlencode "videoId=VIDEO_ID" \
  --data-urlencode "maxResults=20" \
  --data-urlencode "order=relevance" \
  | jq '.items[] | .snippet.topLevelComment.snippet | {author: .authorDisplayName, text: .textDisplay, likes: .likeCount}'
```

## Upload a video (needs `youtube.upload`)

**Confirm with the user before publishing** — show the title, privacy and
file you're about to upload. Uploads are a two-step *resumable* flow:
init with metadata → PUT the bytes.

```bash
FILE="/path/to/video.mp4"
TITLE="My title"
DESC="My description"
# privacyStatus: public | unlisted | private
read -r -d '' META <<JSON
{"snippet":{"title":"$TITLE","description":"$DESC","categoryId":"22"},
 "status":{"privacyStatus":"unlisted","selfDeclaredMadeForKids":false}}
JSON

# 1. Init resumable session -> capture the upload URL from the Location header.
UPLOAD_URL=$(curl -sS -D - -o /dev/null \
  -H "Authorization: Bearer $GOOGLE_YOUTUBE_TOKEN" \
  -H "Content-Type: application/json; charset=UTF-8" \
  -H "X-Upload-Content-Type: video/*" \
  -X POST "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status" \
  -d "$META" | tr -d '\r' | awk '/^[Ll]ocation:/{print $2}')

# 2. Upload the bytes -> returns the created video resource (has .id).
curl -sS -H "Authorization: Bearer $GOOGLE_YOUTUBE_TOKEN" \
  -H "Content-Type: video/*" \
  -X PUT --upload-file "$FILE" "$UPLOAD_URL" \
  | jq '{id: .id, url: ("https://www.youtube.com/watch?v=" + .id), privacy: .status.privacyStatus}'
```

`categoryId` `22` = "People & Blogs" (a safe default). To set a custom
thumbnail (needs the file to be processed first), call
`POST /upload/youtube/v3/thumbnails/set?videoId=VIDEO_ID` with the image.

## Gotchas

- **Quota:** the Data API is quota-metered (default 10,000 units/day). A
  `search` costs 100 units; an `upload` costs ~1,600. A burst of searches
  can exhaust the daily quota → `403 quotaExceeded`; surface it plainly.
- **No "my videos" endpoint** — always go via the uploads playlist.
- **`search` results are eventually-consistent** — a freshly uploaded
  video may not appear in `search` for minutes/hours; read it via the
  uploads playlist or by id instead.
- Uploaded videos start in `uploaded`/`processing` state; stats are `0`
  until processing completes.
