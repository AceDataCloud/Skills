---
name: blogger
description: Publish posts to your Blogger blog and read your blogs / posts via the Blogger API v3. Use when the user mentions Blogger, blogspot, publishing a post to their blog, listing their blogs, or updating an existing Blogger post.
when_to_use: |
  Trigger when the user wants to publish a post to their Blogger blog,
  list their blogs, list / read posts on a blog, or update an existing
  post. The connector grants the Blogger scope (read + write). When the
  user asks to "publish" / "post" / "发布" / "发出去", publish it LIVE
  (isDraft=false) directly — only stage a draft when the user explicitly
  asks for a draft or says they want to review it first.
connections: [google/blogger]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Call the **Blogger API v3** with `curl + jq`. The user's OAuth bearer token is
in `$GOOGLE_BLOGGER_TOKEN`; every call needs
`Authorization: Bearer $GOOGLE_BLOGGER_TOKEN`. Base URL:
`https://www.googleapis.com/blogger/v3`.

Errors are `{"error": {"code": ..., "message": ...}}` — show them verbatim.
`401` → token expired, re-connect the Blogger connector.

**Always start by listing the user's blogs** to get a `blogId`:

```bash
curl -sS -H "Authorization: Bearer $GOOGLE_BLOGGER_TOKEN" \
  "https://www.googleapis.com/blogger/v3/users/self/blogs" \
  | jq '.items[] | {id, name, url}'
```

## Publish a post

When the user asks to publish / post / 发布 / 发出去, publish it **live**
with `?isDraft=false` (the default below) — do NOT silently save a draft
and stop. Only pass `?isDraft=true` when the user explicitly asks for a
draft or to review before going public. After publishing, always report
the returned live `url` back to the user.

```bash
BLOG_ID="1234567890"
jq -n --arg t "My title" --arg c "<p>HTML content of the post…</p>" \
  '{kind:"blogger#post", title:$t, content:$c, labels:["ai","video"]}' \
| curl -sS -X POST \
    "https://www.googleapis.com/blogger/v3/blogs/$BLOG_ID/posts/?isDraft=false" \
    -H "Authorization: Bearer $GOOGLE_BLOGGER_TOKEN" \
    -H "Content-Type: application/json" \
    -d @- \
| jq '{id, url, status}'
```

`content` is **HTML** (not Markdown) — convert Markdown to HTML first
(e.g. with `pandoc -f markdown -t html` or a simple converter).

- Publish a staged draft: `POST /blogs/{blogId}/posts/{postId}/publish`.
- Update a post: `PUT /blogs/{blogId}/posts/{postId}` with the same shape.

## List / read posts

```bash
curl -sS -H "Authorization: Bearer $GOOGLE_BLOGGER_TOKEN" \
  "https://www.googleapis.com/blogger/v3/blogs/$BLOG_ID/posts?maxResults=20&status=live" \
  | jq '.items[] | {id, title, url, published}'
```

## Gotchas

- **Enable the Blogger API** on the Google Cloud project backing the OAuth
  client, or calls 403 with `accessNotConfigured`.
- A `403 "Method doesn't allow unregistered callers"` means the request
  carried no token (empty `$GOOGLE_BLOGGER_TOKEN`) — ask the user to
  (re)connect the Blogger connector, don't blame their Google Cloud setup.
- An empty `{"kind":"blogger#blogList"}` (no `items`) means the connected
  Google account owns no blog — tell the user to create one at blogger.com
  or reconnect with the account that has the blog.
- `content` must be HTML; passing raw Markdown will render literally.
- Paginate with `&pageToken=$PAGE_TOKEN` from the previous `.nextPageToken`.
