---
name: facebook
description: Publish text, link or photo posts to your Facebook Page via the Facebook Pages API, and read your Page's recent posts. Use when the user wants to post to their Facebook Page, share a link, publish a photo, or review their own Page posts. Auth uses a Page access token (BYOC). 支持 Facebook 主页文本 / 链接 / 图片发帖。
when_to_use: |
  Trigger when the user wants to publish a post (text, link or photo) to their
  Facebook Page, cross-post an article, or review their own recent Page posts.
  Publishing posts as their real Page — confirm the message + any link/photo
  first. This posts to a Facebook Page, not a personal profile (the Graph API
  cannot post to personal timelines).
connections: [facebook]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Call the **Facebook Graph API** (`graph.facebook.com`) with `curl + jq`. The
connector injects `$FACEBOOK_ACCESS_TOKEN` (a **Page** access token with
`pages_manage_posts` + `pages_read_engagement`) and optionally
`$FACEBOOK_PAGE_ID`. Never echo them.

The Graph API publishes only to a **Facebook Page** you manage — it cannot post
to a personal profile timeline.

### Resolve the Page id

If `$FACEBOOK_PAGE_ID` is set, use it. Otherwise derive it from the token — try
the **Page-token** path first (`/me` is the Page), then fall back to the
**user-token** path (`/me/accounts` → first managed Page), so either token type
the connector accepts resolves cleanly:

```bash
if [ -n "$FACEBOOK_PAGE_ID" ]; then
  PAGE="$FACEBOOK_PAGE_ID"
else
  # Page access token: /me IS the Page
  PAGE=$(curl -sS "https://graph.facebook.com/v21.0/me?fields=id,name&access_token=$FACEBOOK_ACCESS_TOKEN" | jq -r 'select(.name).id // empty')
  if [ -z "$PAGE" ]; then
    # User access token: list the managed Pages, take the first
    PAGE=$(curl -sS "https://graph.facebook.com/v21.0/me/accounts?access_token=$FACEBOOK_ACCESS_TOKEN" | jq -r '.data[0].id // empty')
  fi
fi
echo "page_id=$PAGE"
```

Errors are JSON with `error.message` / `error.code` — show them verbatim.
`401` / `OAuthException` → token expired or missing scope; a null `PAGE` → the
token isn't a Page token / manages no Page (see Gotchas). Reconnect if needed.

> If the user token path is used, `/me/accounts` also returns a per-Page
> `access_token` in `.data[0].access_token`. Prefer that Page token for the
> publish call when the injected token is a user token; a Page's own token is
> what `pages_manage_posts` actually authorizes.

## Publish a text or link post

**Confirm the message (and link, if any) with the user first.** Post to
`/{page-id}/feed`:

```bash
# Text-only post
curl -sS -X POST "https://graph.facebook.com/v21.0/$PAGE/feed" \
  --data-urlencode "message=One endpoint → posters, cards, mockups. #AI #API" \
  -d "access_token=$FACEBOOK_ACCESS_TOKEN" | jq .
# → {"id":"<PAGE_ID>_<POST_ID>"}

# Link post — Facebook renders a link preview card from the URL
curl -sS -X POST "https://graph.facebook.com/v21.0/$PAGE/feed" \
  --data-urlencode "message=Read our new guide 👇" \
  -d "link=https://acedata.cloud/blog/xxxx" \
  -d "access_token=$FACEBOOK_ACCESS_TOKEN" | jq .
```

## Publish a photo post

Post to `/{page-id}/photos` with a **public image URL** (Facebook server-side
fetches it); `caption` is the post text:

```bash
curl -sS -X POST "https://graph.facebook.com/v21.0/$PAGE/photos" \
  -d "url=https://cdn.acedata.cloud/xxxx.jpg" \
  --data-urlencode "caption=One endpoint → posters, cards, mockups. #AI #API" \
  -d "access_token=$FACEBOOK_ACCESS_TOKEN" | jq .
# → {"id":"<PHOTO_ID>","post_id":"<PAGE_ID>_<POST_ID>"}
```

To attach **multiple photos** to one post: upload each with `published=false` to
get its media id, then create the feed post with
`attached_media[0]={"media_fbid":"<ID1>"}` … for each.

## Get the post permalink

Use the returned `post_id` (or `id`) to fetch the live URL to hand back:

```bash
curl -sS "https://graph.facebook.com/v21.0/<PAGE_ID>_<POST_ID>?fields=permalink_url&access_token=$FACEBOOK_ACCESS_TOKEN" | jq -r .permalink_url
```

## Read recent Page posts

```bash
curl -sS "https://graph.facebook.com/v21.0/$PAGE/posts?fields=id,message,created_time,permalink_url&limit=10&access_token=$FACEBOOK_ACCESS_TOKEN" | jq .
```

## Gotchas

- **Pages only, not profiles** — the Graph API cannot publish to a personal
  timeline. If the user asks to post to their profile, explain this limitation.
- **Page token, not user token** — publishing needs a Page access token with
  `pages_manage_posts`. If you only have a user token, resolve the Page token via
  `/me/accounts` (see above). A `(#200)` permissions error means the token lacks
  `pages_manage_posts` or the user isn't an admin of the Page.
- **Photo URL must be public** on a server Facebook can reach; local files won't
  work. Host on cdn.acedata.cloud first.
- **Page Publishing Authorization (PPA):** some Pages must complete PPA before API
  publishing works — surface the API error verbatim if it mentions PPA.
- **Token expiry:** a Page token derived from a short-lived user token expires
  fast. If posting 401s soon after connecting, the user needs a long-lived Page
  token — surface the `OAuthException` verbatim and suggest reconnecting.
- API version: keep the `vXX.0` path current if you hit a version/deprecation error.

## Record the output

After you successfully publish and obtain the live permalink, call the built-in
`publish_artifact` tool ONCE so the user can track it in **My Outputs**:

```
publish_artifact(kind="post", channel="facebook", title="<title>", url="<the REAL permalink>", status="delivered")
```

Use the real returned URL — never fabricate one. Call it once per published item,
only after delivery is confirmed; skip it (or use `status="failed"`) if publishing failed.
See `_shared/artifacts.md`.
