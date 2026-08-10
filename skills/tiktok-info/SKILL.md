---
name: tiktok-info
description: Search TikTok users/videos and retrieve public TikTok profile, post, and video details through AceDataCloud's TikTok Information API. Use for public TikTok discovery and analysis, not for uploading or publishing videos.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# TikTok Information

Discover public TikTok users and videos through AceDataCloud's TikTok
Information API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/tiktok/search \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"type":"user","keywords":"AceData"}'
```

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /tiktok/search` | Search TikTok users or videos by keyword |
| `POST /tiktok/user` | Get public user details by `unique_id` or `user_id` |
| `POST /tiktok/posts` | Get a user's public posts by `unique_id` or `user_id` |
| `POST /tiktok/video` | Get details for a TikTok video URL |

## Workflows

### Search users or videos

```json
POST /tiktok/search
{
  "type": "video",
  "keywords": "ai music",
  "region": "us",
  "sort_type": 0,
  "publish_time": 7
}
```

### Get user details

```json
POST /tiktok/user
{"unique_id": "tiktok"}
```

### List a user's posts

```json
POST /tiktok/posts
{"unique_id": "tiktok", "cursor": "0"}
```

### Get video details

```json
POST /tiktok/video
{"video_url": "https://www.tiktok.com/@tiktok/video/7106658991907802411"}
```

## Parameters

| Endpoint | Parameter | Values | Description |
|----------|-----------|--------|-------------|
| `/tiktok/search` | `type` | `user`, `video` | Search resource type (required) |
| `/tiktok/search` | `keywords` | string | Search query (required) |
| `/tiktok/search` | `cursor` | integer | Pagination cursor |
| `/tiktok/search` | `region` | `us`, `jp`, `kr`, `vn`, `br`, `ru` | Region filter |
| `/tiktok/search` | `sort_type` | `0`, `1`, `3` | Sort mode |
| `/tiktok/search` | `publish_time` | `0`, `1`, `24`, `7`, `30`, `90`, `180` | Publish-time filter |
| `/tiktok/user`, `/tiktok/posts` | `unique_id` / `user_id` | string | Public user identifier |
| `/tiktok/posts` | `cursor` | string | Pagination cursor |
| `/tiktok/video` | `video_url` | URL | TikTok video URL (required) |
| `/tiktok/video` | `original_quality` | integer | Request original-quality video data when available |

## Gotchas

- This is the AceDataCloud public information API at
  `https://api.acedata.cloud/tiktok/*`; it is separate from the OAuth-based
  TikTok upload/drafts connector skill.
- The API reads public TikTok information only. Do not use it to publish or
  upload videos.
- Use `cursor` values from prior responses for pagination.
