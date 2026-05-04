---
name: wechat-official-account
description: Generate articles, manage drafts, publish to «发表记录», send customer-service messages, manage menus and pull stats on a WeChat Official Account (微信公众号 / 服务号 / 订阅号) via the WeChat MP server-side API. Use when the user mentions 公众号, 服务号, 订阅号, mp.weixin.qq.com, AppID/AppSecret of a WeChat Official Account, or asks to draft / publish / send a customer message via WeChat.
when_to_use: |
  Trigger when the user wants to do anything with their WeChat
  Official Account: turn a chat conversation into a draft article,
  list / publish / delete drafts, send a 48-hour-window customer
  service message to a follower (by openid), upload images that will
  appear inside an article body, manage the bottom menu, look up
  follower stats, etc.
connections: [wechat]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

We drive the [WeChat MP server-side API](https://developers.weixin.qq.com/doc/service/guide/) with `curl + jq`. Unlike OAuth-bearer connectors, WeChat MP uses a two-step flow:

1. Exchange `AppID + AppSecret` for an `access_token` (TTL 7200s, **global limit ≈ 2000 calls/day per app**).
2. Pass that `access_token` as a **query string parameter** on every other call.

The user's credentials are in `$WECHAT_APP_ID` and `$WECHAT_APP_SECRET`. **Never log or echo `$WECHAT_APP_SECRET`** — treat it like a password.

The WeChat MP API returns standard JSON. **Errors are returned with HTTP 200**; the body looks like `{"errcode": 40013, "errmsg": "invalid appid"}`. `errcode == 0` means success — show the original `errmsg` to the user verbatim on any non-zero code.

## Important constraints — surface these to the user before they're surprised

- **IP whitelist**: every API call's source IP must be in this app's IP whitelist (公众平台 → 设置与开发 → 基本配置 → IP 白名单). If you see `errcode 40164` ("invalid ip"), the worker's egress IP isn't whitelisted; tell the user to add the IP shown in `errmsg` and retry.
- **Verified account required for publishing**: as of 2025-07, only **verified (已认证) corporate-subject** accounts can call `freepublish/*` and `mass/*`. Personal-subject accounts and unverified corporate accounts get a permission error. Drafts (`draft/*`) and customer messages (`message/custom/*`) usually work without verification.
- **Group-send quota is harsh**: 服务号 = 4 sends/month, 订阅号 = 1 send/day. Treat `freepublish/submit` and `mass/sendall` like a **destructive operation** — *always* confirm with the user before calling them, even if instructions say "publish it". Default to creating a draft and pasting the draft URL.
- **Customer-service window is 48 hours**: `message/custom/send` only works for a follower whose `openid` interacted with the account in the last 48 hours. Outside that window you get `errcode 45015`.

## Recipes

### Step 0 — get an access_token (do this first, cache the result)

```sh
# Cache to /tmp so subsequent calls in the same session reuse it.
TOKEN_CACHE="/tmp/wx-mp-token-${WECHAT_APP_ID}.json"

# Reuse cached token if it's still valid (we conservatively refresh
# 5 minutes early to avoid edge-of-window failures).
NOW=$(date +%s)
if [ -f "$TOKEN_CACHE" ] && [ "$(jq -r '.exp_at // 0' "$TOKEN_CACHE")" -gt "$((NOW + 300))" ]; then
  WECHAT_ACCESS_TOKEN=$(jq -r '.access_token' "$TOKEN_CACHE")
else
  RESP=$(curl -sS "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${WECHAT_APP_ID}&secret=${WECHAT_APP_SECRET}")
  WECHAT_ACCESS_TOKEN=$(echo "$RESP" | jq -r '.access_token // empty')
  if [ -z "$WECHAT_ACCESS_TOKEN" ]; then
    echo "Failed to fetch access_token: $RESP" >&2
    exit 1
  fi
  EXPIRES=$(echo "$RESP" | jq -r '.expires_in // 7200')
  jq -nc --arg t "$WECHAT_ACCESS_TOKEN" --argjson e "$((NOW + EXPIRES))" \
    '{access_token:$t, exp_at:$e}' > "$TOKEN_CACHE"
fi
echo "OK token=${WECHAT_ACCESS_TOKEN:0:8}…"
```

If the response is `{"errcode": 40164, ...}` (invalid IP) or `{"errcode": 40013, ...}` (invalid appid) — surface that error to the user; it means the connector setup itself is wrong, not the request.

### Verify the connection (always run this once before complex operations)

```sh
# Pull basic public-account self-info; cheapest call that proves the token works.
curl -sS "https://api.weixin.qq.com/cgi-bin/account/getaccountbasicinfo?access_token=${WECHAT_ACCESS_TOKEN}" | jq
```

### Upload an image to use *inside* an article body (returns a public URL)

This is for `<img src="...">` tags inside the article HTML. The returned `url` is hosted by Tencent and works in published articles.

```sh
curl -sS -X POST \
  "https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=${WECHAT_ACCESS_TOKEN}" \
  -F "media=@/path/to/your-image.jpg"
# → {"url": "http://mmbiz.qpic.cn/..."}
```

Limits: ≤ 1 MB, JPG/PNG only, no count limit on this endpoint.

### Upload a thumbnail (needed as the article cover)

```sh
curl -sS -X POST \
  "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=${WECHAT_ACCESS_TOKEN}&type=thumb" \
  -F "media=@/path/to/cover.jpg" | jq '{media_id, url}'
# → {"media_id": "MEDIA_ID", "url": "http://mmbiz.qpic.cn/..."}
```

The `media_id` you get back is what you pass as `thumb_media_id` when creating a draft.
Recommended cover dimensions: 900×500 px, JPG, < 64 KB ideally.

### Create a draft (the safe default — *do not* directly publish)

```sh
TITLE="Q1 product update"
AUTHOR="Acme Inc."
THUMB_MEDIA_ID="MEDIA_ID_FROM_PREVIOUS_STEP"
CONTENT_HTML='<p>欢迎关注我们的最新动态。</p><p><img src="http://mmbiz.qpic.cn/..."></p><p>更多内容请见底部「阅读原文」。</p>'
DIGEST="Q1 has been a wild ride — here's what shipped."
SOURCE_URL="https://example.com/q1-recap"   # optional; populates 「阅读原文」, leave empty to omit

PAYLOAD=$(jq -nc \
  --arg title       "$TITLE" \
  --arg author      "$AUTHOR" \
  --arg thumb       "$THUMB_MEDIA_ID" \
  --arg content     "$CONTENT_HTML" \
  --arg digest      "$DIGEST" \
  --arg source_url  "$SOURCE_URL" \
  '{articles: [{
    article_type: "news",
    title: $title,
    author: $author,
    thumb_media_id: $thumb,
    content: $content,
    digest: $digest,
    content_source_url: $source_url,
    need_open_comment: 0,
    only_fans_can_comment: 0
  }]}')

curl -sS -X POST \
  "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=${WECHAT_ACCESS_TOKEN}" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-raw "$PAYLOAD" | jq
# → {"media_id": "DRAFT_MEDIA_ID"}
```

Tell the user: *"Draft created. Open https://mp.weixin.qq.com → 草稿箱 to review and tap «发表» from there."* — that's the safest path because the user controls the publish click in WeChat's own UI.

### List drafts (newest first)

```sh
curl -sS -X POST \
  "https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=${WECHAT_ACCESS_TOKEN}" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-raw '{"offset": 0, "count": 20, "no_content": 1}' \
  | jq '.item[] | {media_id, update_time, title: .content.news_item[0].title}'
```

### Get the full content of one draft

```sh
DRAFT_MEDIA_ID="..."
curl -sS -X POST \
  "https://api.weixin.qq.com/cgi-bin/draft/get?access_token=${WECHAT_ACCESS_TOKEN}" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-raw "$(jq -nc --arg m "$DRAFT_MEDIA_ID" '{media_id: $m}')" | jq
```

### Update an existing draft

```sh
curl -sS -X POST \
  "https://api.weixin.qq.com/cgi-bin/draft/update?access_token=${WECHAT_ACCESS_TOKEN}" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-raw "$(jq -nc --arg m "$DRAFT_MEDIA_ID" --arg t "Updated title" --arg c "<p>new body</p>" --arg th "$THUMB_MEDIA_ID" '
    {media_id: $m, index: 0, articles: {
      title: $t, content: $c, thumb_media_id: $th
    }}')" | jq
```

### Publish a draft to «发表记录» — DESTRUCTIVE, confirm before calling

```sh
# Eats one of the monthly publish slots. Always echo back to the user
# what's about to go live and require an explicit "yes" confirmation
# in conversation BEFORE invoking this.
curl -sS -X POST \
  "https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token=${WECHAT_ACCESS_TOKEN}" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-raw "$(jq -nc --arg m "$DRAFT_MEDIA_ID" '{media_id: $m}')" | jq
# → {"errcode": 0, "msg_data_id": ..., "publish_id": "..."}
```

Then poll publish status (publishing is async, takes ~5-30 seconds):

```sh
PUBLISH_ID="..."
curl -sS -X POST \
  "https://api.weixin.qq.com/cgi-bin/freepublish/get?access_token=${WECHAT_ACCESS_TOKEN}" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-raw "$(jq -nc --arg p "$PUBLISH_ID" '{publish_id: $p}')" | jq '{publish_status, fail_idx, article_id, article_url: .article_detail.item[0].article_url}'
# publish_status: 0 = success, 1 = publishing, 2 = original-check-failed,
#                 3 = failed, 4 = published-but-removed, 5 = unverified-removed
```

When `publish_status == 0`, return `article_detail.item[0].article_url` to the user — that's the canonical https://mp.weixin.qq.com/s/... URL.

### List already-published articles

```sh
curl -sS -X POST \
  "https://api.weixin.qq.com/cgi-bin/freepublish/batchget?access_token=${WECHAT_ACCESS_TOKEN}" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-raw '{"offset": 0, "count": 20, "no_content": 1}' \
  | jq '.item[] | {article_id, update_time, title: .content.news_item[0].title, url: .content.news_item[0].url}'
```

### Send a customer-service message (one specific follower, 48h window)

```sh
OPENID="oXXXXXXXXXXXXXXXXX"   # the recipient follower's openid
TEXT="Hi! Your subscription has been renewed. Thanks for sticking with us."

curl -sS -X POST \
  "https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token=${WECHAT_ACCESS_TOKEN}" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-raw "$(jq -nc --arg u "$OPENID" --arg t "$TEXT" '
    {touser: $u, msgtype: "text", text: {content: $t}}')" | jq
```

`errcode 45015` = recipient hasn't messaged the account in the last 48h — explain that to the user; there's nothing the API can do about it.

To send an article card via customer message, change to `msgtype: "mpnews"` with `mpnews: {media_id: "..."}` (use `material/add_news` to first create a permanent news media_id).

### Pull follower-growth + read stats

```sh
BEGIN="2026-04-25"
END="2026-05-01"   # max 7-day window for getusersummary

# New / unsubscribed / cumulative followers per day
curl -sS -X POST \
  "https://api.weixin.qq.com/datacube/getusersummary?access_token=${WECHAT_ACCESS_TOKEN}" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-raw "$(jq -nc --arg b "$BEGIN" --arg e "$END" '{begin_date: $b, end_date: $e}')" \
  | jq '.list[] | {date: .ref_date, new: .new_user, lost: .cancel_user, source: .user_source}'

# Article reads per day (max 3-day window for getuserread)
curl -sS -X POST \
  "https://api.weixin.qq.com/datacube/getuserread?access_token=${WECHAT_ACCESS_TOKEN}" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-raw "$(jq -nc --arg b "$BEGIN" --arg e "$BEGIN" '{begin_date: $b, end_date: $e}')" | jq
```

`datacube/*` requires an authenticated (已认证) account with the data-cube permission.

### Manage the bottom menu

```sh
# Read current menu
curl -sS "https://api.weixin.qq.com/cgi-bin/menu/get?access_token=${WECHAT_ACCESS_TOKEN}" | jq

# Replace the menu (max 3 top-level buttons; each top-level button can have ≤ 5 sub-buttons)
MENU=$(jq -nc '{
  button: [
    {type: "click", name: "今日推荐", key: "DAILY_REC"},
    {name: "更多",
     sub_button: [
       {type: "view", name: "官网",   url: "https://example.com"},
       {type: "view", name: "联系我们", url: "https://example.com/contact"}
     ]}
  ]
}')
curl -sS -X POST \
  "https://api.weixin.qq.com/cgi-bin/menu/create?access_token=${WECHAT_ACCESS_TOKEN}" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-raw "$MENU" | jq
# → {"errcode": 0, "errmsg": "ok"}
```

### Get the follower list (paginated by next_openid)

```sh
NEXT=""
curl -sS "https://api.weixin.qq.com/cgi-bin/user/get?access_token=${WECHAT_ACCESS_TOKEN}&next_openid=${NEXT}" \
  | jq '{total, count, openids: .data.openid, next: .next_openid}'
# Loop: pass the returned `next_openid` as NEXT until count < 10000.
```

For each openid, batch-fetch profile (≤ 100 per call):

```sh
curl -sS -X POST \
  "https://api.weixin.qq.com/cgi-bin/user/info/batchget?access_token=${WECHAT_ACCESS_TOKEN}" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-raw '{"user_list": [{"openid": "OPENID1", "lang": "zh_CN"}]}' \
  | jq '.user_info_list[] | {openid, nickname, subscribe_time, tagid_list}'
```

## HTML rules for article `content`

The `content` field in `draft/add` accepts a *subset* of HTML, not full web HTML:

- Allowed: `<p>`, `<span>`, `<strong>`, `<em>`, `<a href>`, `<img src>`, `<br>`, `<h1>`–`<h3>`, `<ul>/<ol>/<li>`, `<blockquote>`, `<section>`.
- **Inline styles only** (`<p style="...">`) — no `<style>` blocks, no `<link>` to external CSS.
- All `<img>` `src` URLs **must** be either previously-uploaded `mmbiz.qpic.cn` URLs (from `media/uploadimg`) or already-published `mmbiz` URLs. WeChat strips images hosted on third-party domains.
- Total content size limit: ~ 20 K characters (HTML included).

## Common errcode cheat-sheet

| errcode | meaning | what to tell the user |
|---|---|---|
| 0 | success | — |
| 40001 | invalid access_token | Token expired mid-call; flush `$TOKEN_CACHE` and retry |
| 40013 | invalid appid | The AppID in the connector is wrong — re-add the connection |
| 40164 | source IP not in whitelist | Add the IP shown in `errmsg` to 公众平台 → 设置与开发 → 基本配置 → IP白名单 |
| 41001 | missing access_token | Bug — you forgot to pass `?access_token=...` |
| 45009 | API daily quota exceeded | Try again tomorrow; the per-app daily quota was hit |
| 45015 | response message out of 48h | Customer-service window has closed for this openid; can't recover via API |
| 48001 | api unauthorized | Account doesn't have permission for this endpoint (e.g. publish without 认证); see the doc URL in errmsg |
| 61450 | system error | Tencent-side flake; retry once after a 1-second backoff |

## Why we use bare `curl + jq` (not an SDK)

Skill bodies must be self-contained shell. Calling `pip install wechatpy` is not allowed in the sandbox, and the API surface here is small (15-ish endpoints) and stable since 2018. The python SDKs ([wechatpy](https://github.com/wechatpy/wechatpy), werobot) are useful references for parameter shapes, but every recipe above is a direct call to the documented endpoint — the SDKs are just thin wrappers around the same JSON.
