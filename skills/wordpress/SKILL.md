---
name: wordpress
description: Publish and manage posts on a self-hosted WordPress site via the WordPress REST API. Use when the user mentions WordPress, wp-admin, publishing / updating a blog post, managing categories or tags, or uploading media to their own WordPress site.
when_to_use: |
  Trigger when the user wants to do anything with their self-hosted
  WordPress site: turn a chat conversation into a published or draft
  post, update an existing post, list recent posts, create / list
  categories and tags, or upload a media file for use inside a post.
  This skill is for self-hosted WordPress (Application Password auth),
  not WordPress.com.
connections: [wordpress]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Drive the **WordPress REST API** (`/wp-json/wp/v2`) with `curl + jq`.

The user's self-hosted WordPress credentials are injected as env vars:

- `$WORDPRESS_SITE_URL` — site root, e.g. `https://blog.example.com`
- `$WORDPRESS_USERNAME` — the WordPress login username
- `$WORDPRESS_APP_PASSWORD` — an **Application Password** (WP 5.6+ core), NOT the
  login password. Treat it like a secret — **never log or echo it.**

Auth is HTTP Basic (`username:app_password`) over HTTPS. Set up a reusable base
once, then every call reuses it:

```bash
# Normalize the site URL (strip a trailing slash) and build the API base.
SITE="${WORDPRESS_SITE_URL%/}"
API="$SITE/wp-json/wp/v2"
# -u sends HTTP Basic auth; --fail-with-body surfaces the JSON error body on 4xx/5xx.
WP=(curl -sS --fail-with-body -u "$WORDPRESS_USERNAME:$WORDPRESS_APP_PASSWORD")
```

Errors come back as `{"code": "...", "message": "...", "data": {"status": 401}}` —
show `message` verbatim. Common codes:

| HTTP | Meaning | What to tell the user |
|------|---------|-----------------------|
| 401 | `incorrect_password` / bad Basic auth | Application Password wrong or revoked → regenerate it and reconnect the WordPress connector |
| 403 | `rest_cannot_create` / insufficient role | The user's role can't publish; needs Author/Editor/Admin, or Application Passwords are disabled on the site |
| 404 | `rest_no_route` | REST API disabled or a security plugin blocks `/wp-json` → the user must re-enable it |
| 400 | `rest_invalid_param` | Bad field (e.g. unknown category id) → fix and retry |

> **`content` is HTML, not Markdown.** Convert Markdown to HTML first
> (`pandoc -f markdown -t html`, or a simple converter). Raw Markdown renders literally.

## Step 0 — verify the connection first

```bash
"${WP[@]}" "$API/users/me" | jq '{id, name, slug, roles: (.roles // [])}'
```

A 200 with your user object confirms the site URL, username, and Application
Password all work. If this fails, stop and surface the error — don't attempt writes.

## Publish or draft a post

**Publishing is public and hard to undo — confirm with the user before using
`status=publish`.** Default to `status=draft` and hand back the edit link.

```bash
jq -n --arg t "国内如何稳定调用 Claude API" \
      --arg c "<p>正文 HTML……</p>" \
      --arg s "draft" \
  '{title:$t, content:$c, status:$s}' \
| "${WP[@]}" -X POST "$API/posts" \
    -H "Content-Type: application/json" -d @- \
| jq '{id, status, link, edit: "\(env.WORDPRESS_SITE_URL)/wp-admin/post.php?action=edit&post=\(.id)"}'
```

With categories / tags / excerpt (ids come from the endpoints below):

```bash
jq -n --arg t "标题" --arg c "<p>正文</p>" --arg e "一句话摘要" \
  '{title:$t, content:$c, excerpt:$e, status:"draft",
    categories:[5], tags:[12,34]}' \
| "${WP[@]}" -X POST "$API/posts" -H "Content-Type: application/json" -d @- \
| jq '{id, status, link}'
```

- Publish an existing draft: `POST $API/posts/<id>` body `{"status":"publish"}`.
- Update a post: `POST $API/posts/<id>` with any subset of fields (WP REST uses
  POST, not PUT, for updates).
- Delete (trash) a post: `"${WP[@]}" -X DELETE "$API/posts/<id>"`.

## List / read posts

```bash
"${WP[@]}" "$API/posts?per_page=10&status=publish,draft&_fields=id,title,status,link,date" \
  | jq '.[] | {id, title: .title.rendered, status, link, date}'
```

Paginate with `&page=2`; the total page count is in the `X-WP-TotalPages`
response header (add `-D -` to see headers).

## Categories & tags (get or create ids)

```bash
# List existing
"${WP[@]}" "$API/categories?per_page=100&_fields=id,name,slug" | jq '.[] | {id, name}'
"${WP[@]}" "$API/tags?per_page=100&_fields=id,name,slug"       | jq '.[] | {id, name}'

# Create one (returns its id)
jq -n --arg n "AI 教程" '{name:$n}' \
| "${WP[@]}" -X POST "$API/categories" -H "Content-Type: application/json" -d @- \
| jq '{id, name}'
```

Creating a term that already exists returns
`{"code":"term_exists", ... "data":{"status":400,"term_id":<id>}}` — reuse
`.data.term_id` instead of failing.

## Upload media (featured image / in-body image)

```bash
FILE="./cover.png"
NAME="$(basename "$FILE")"
MEDIA_ID=$("${WP[@]}" -X POST "$API/media" \
  -H "Content-Disposition: attachment; filename=\"$NAME\"" \
  -H "Content-Type: image/png" \
  --data-binary @"$FILE" | jq -r '.id')
echo "media id=$MEDIA_ID"
# Attach as the post's featured image:
#   add  "featured_media": <MEDIA_ID>  to the post body.
```

## Gotchas

- **HTTPS + Application Passwords are required.** On plain `http://`, WordPress
  disables Application Passwords → every call 401s. Tell the user to enable HTTPS.
- **A security plugin / host may block `/wp-json`** (Wordfence, "disable REST
  API" plugins, some managed hosts). Symptom: 404 `rest_no_route` or an HTML
  login page instead of JSON. The user must allow REST API access.
- **The Application Password contains spaces** (e.g. `abcd efgh ijkl mnop`).
  Keep them — `curl -u` handles the spaces fine; don't strip them.
- **Never publish silently.** Even if the user says "post it", prefer creating a
  draft and returning the `wp-admin` edit link unless they explicitly asked to
  go live.


## Record the output

After you successfully publish and obtain the live result URL, call the built-in
`publish_artifact` tool ONCE so the user can track this deliverable in **My Outputs**:

```
publish_artifact(kind="article", channel="wordpress", title="<title>", url="<the REAL returned URL>", status="delivered")
```

Use the real returned URL — never fabricate one. Call it once per published item,
only after delivery is confirmed; skip it (or use `status="failed"`) if publishing failed.
See `_shared/artifacts.md`.
