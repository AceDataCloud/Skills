---
name: vk
description: Publish posts to your VK (ВКонтакте) profile or community wall and read your own recent posts, via the official VK API (wall.post / wall.get). Use when the user wants to post to VK, cross-post an article for a Russian-speaking audience, or list their own recent VK wall posts with engagement. Auth uses a VK access token (community access key recommended).
when_to_use: |
  Trigger when the user wants to publish content to their VK wall or community,
  or review their own recent VK posts. VK's user-token OAuth flows were disabled
  in June 2024, so the connector stores a long-lived **community access key**
  (VK community → Manage → Settings → API usage, with the `wall` right). Posting
  to a community wall uses a negative owner_id + from_group=1. Confirm the post
  text with the user before publishing.
connections: [vk]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Call the **VK API** with `curl + jq`. The token is injected as `$VK_ACCESS_TOKEN`
and is passed in the `Authorization: Bearer` header. **Every** VK API call also
requires the `v` (API version) query parameter — use `v=5.199`. Base URL:
`https://api.vk.com/method/<method>`.

VK always returns HTTP 200; success is `{"response": ...}` and failure is
`{"error":{"error_code":<n>,"error_msg":"<detail>"}}` — always check for `.error`
and show `error_msg` verbatim. Common codes: `5` = auth failed (token wrong or
revoked → user must re-connect the VK connector), `214` = access to adding post
denied (the token lacks the `wall` right — a community access key with `wall` is
required), `15`/`203` = access denied to that owner.

## Step 1 — identify who you can post as

A **community access key** posts on the community wall: `owner_id` must be the
**negative** community id and you pass `from_group=1`. Resolve the community id
from the token:

```bash
curl -sS "https://api.vk.com/method/groups.getById?v=5.199" \
  -H "Authorization: Bearer $VK_ACCESS_TOKEN" \
  | jq '.response, .error'
```

Take the group `id` (e.g. `123456`) → `owner_id` is `-123456`. (For a personal
user token, `owner_id` is your positive user id from `users.get`, and you omit
`from_group`.)

## Post to the wall

**Confirm the message text with the user before posting.** The post must have
text and/or attachments.

```bash
OWNER_ID="-123456"   # negative = community; from_group=1 posts as the community
MSG="Пример поста через VK API. #ai"
curl -sS -G "https://api.vk.com/method/wall.post" \
  -H "Authorization: Bearer $VK_ACCESS_TOKEN" \
  --data-urlencode "v=5.199" \
  --data-urlencode "owner_id=$OWNER_ID" \
  --data-urlencode "from_group=1" \
  --data-urlencode "message=$MSG" \
  | jq '.response, .error'
```

Success returns `{"response":{"post_id":<id>}}`. The public URL is
`https://vk.com/wall<OWNER_ID>_<post_id>` (e.g. `https://vk.com/wall-123456_17`).

- Hashtags (`#tag`) and plain URLs in `message` are rendered/clickable natively —
  no facet/offset handling needed (unlike Bluesky).
- Attach media/links with `attachments` (comma-separated), format
  `{type}{owner_id}_{media_id}` (e.g. `photo-123456_789`) or a single external
  URL. Only **one** link may be attached; more than one link → error 222.
- `publish_date` (Unix timestamp) schedules a deferred post.
- Always send Cyrillic `message` via `--data-urlencode` so it isn't mangled.

## List my recent wall posts + engagement

```bash
OWNER_ID="-123456"
curl -sS -G "https://api.vk.com/method/wall.get" \
  -H "Authorization: Bearer $VK_ACCESS_TOKEN" \
  --data-urlencode "v=5.199" \
  --data-urlencode "owner_id=$OWNER_ID" \
  --data-urlencode "count=20" \
  | jq '.error, (.response.items[]? | {id,
        text,
        likes: .likes.count,
        reposts: .reposts.count,
        comments: .comments.count,
        views: .views.count,
        date})'
```

`count` max 100. Combine `owner_id` + a post `id` to build the URL
`https://vk.com/wall<owner_id>_<id>`.

## Delete a post

```bash
OWNER_ID="-123456"; POST_ID="17"
curl -sS -G "https://api.vk.com/method/wall.delete" \
  -H "Authorization: Bearer $VK_ACCESS_TOKEN" \
  --data-urlencode "v=5.199" \
  --data-urlencode "owner_id=$OWNER_ID" \
  --data-urlencode "post_id=$POST_ID" \
  | jq '.response, .error'
```

## Gotchas

- **`v` is mandatory** on every call — omitting it returns an error.
- **User tokens can't be freshly minted via OAuth** (Implicit / Authorization
  Code flows for user tokens were disabled 2024-06); use a **community access
  key** (unlimited lifetime, created in the community's API settings) with the
  `wall` right.
- Posting as the community requires both `owner_id` negative **and**
  `from_group=1`.
- Rate/anti-spam: repeated identical posts or too-frequent posting can hit codes
  like `214`/`219` — space posts out.
