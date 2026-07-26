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
allowed_tools: [Bash, publish_artifact]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.1"
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

> **Don't add `-L`/`--location` to these calls.** A redirect usually means the
> site URL is wrong. curl strips the `Authorization` header when a redirect
> crosses host or scheme (e.g. `http`→`https`, apex→`www`) — exactly the cases
> that occur here — so the followed request runs **unauthenticated** and can
> return the site's HTML page with HTTP 200: it looks like success but wrote
> nothing. Fix the URL instead (see the `/wp-json` gotcha below).


Errors come back as `{"code": "...", "message": "...", "data": {"status": 401}}` —
show `message` verbatim. Common codes:

| HTTP | Meaning | What to tell the user |
|------|---------|-----------------------|
| 401 | `incorrect_password` / bad Basic auth | Application Password wrong or revoked → regenerate it and reconnect the WordPress connector |
| 401 | `rest_not_logged_in` on a plain-`http://` site | Application Passwords are disabled without HTTPS → the user must enable HTTPS |
| 403 | `rest_cannot_create` / insufficient role | The user's role can't publish; needs Author/Editor/Admin, or Application Passwords are disabled on the site |
| 404 | `rest_no_route` | REST API disabled or a security plugin blocks `/wp-json` → the user must re-enable it |
| 400 | `rest_invalid_param` | Bad field (e.g. unknown category id) → fix and retry |
| 500 | `rest_upload_sideload_error` | `wp-content/uploads` isn't writable by the web server → the user must fix directory permissions |

> **`content` is HTML, not Markdown.** Raw Markdown renders literally. `pandoc` is
> **not installed** — convert with Python's `markdown` package (preinstalled in the
> sandbox). If the import ever fails, `pip install markdown` first, then:
>
> ```bash
> HTML=$(python3 -c "
> import sys, markdown
> print(markdown.markdown(sys.stdin.read(), extensions=['fenced_code','tables']))
> " <<'MD'
> ## 标题
>
> 正文 **粗体**
> MD
> )
> ```


## Step 0 — verify the connection first

```bash
"${WP[@]}" "$API/users/me?context=edit" | jq '{id, name, slug, roles}'
```

`context=edit` is required — without it WP omits `roles`/`capabilities` entirely,
so you cannot tell whether the account may publish. A 200 with `roles` containing
`administrator`, `editor` or `author` confirms the site URL, username, Application
Password **and** publish permission. If this fails, stop and surface the error —
don't attempt writes.

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
- Schedule a post: `{"status":"future","date_gmt":"2030-01-01T00:00:00"}` (UTC,
  no trailing `Z`).

## SEO fields that actually matter

WordPress core emits `<link rel="canonical">` on its own but ships **no meta
description tag at all** — that only appears if the site runs an SEO plugin
(Yoast, Rank Math, SEOPress) or a theme that renders one. Those consume the
post's `excerpt`, so setting `excerpt` is what makes a good description possible;
it does nothing on a bare core install. For an SEO post always set:

| Field | Why |
|---|---|
| `slug` | The permalink. Set it explicitly to a short ASCII keyword phrase — otherwise a CJK title becomes a percent-encoded URL. |
| `excerpt` | Source for the SEO plugin's meta description and for list-page summaries. One sentence. |
| `categories` / `tags` | Internal linking + topic clustering. |
| `featured_media` | Social/OG card image. |
| media `alt_text` | Image SEO + accessibility. Set it on the media object (below). |


```bash
jq -n --arg s "claude-api-guide" --argjson c 3 --argjson m 9 \
  '{title:"如何稳定调用 Claude API：完整对接指南",
    slug:$s,
    content:"<h2>小标题</h2><p>正文</p>",
    excerpt:"一句话摘要，用于 meta description。",
    status:"publish", categories:[$c], featured_media:$m}' \
| "${WP[@]}" -X POST "$API/posts" -H "Content-Type: application/json" -d @- \
| jq '{id, status, slug, link}'
```

## Before publishing: check for a duplicate

**WordPress will NOT reject a duplicate slug — it silently appends `-2`,** so an
unattended/scheduled run that reposts the same article creates an endless trail of
near-identical URLs that compete with each other in search. Always pre-check:

```bash
SLUG="claude-api-guide"
# Fail CLOSED at BOTH steps: a failed request, or a 200 that isn't a JSON array
# (HTML from a redirect/permalink issue, or an error object), must abort — never
# fall through and create the duplicate this check exists to prevent.
if ! LOOKUP=$("${WP[@]}" "$API/posts?slug=$SLUG&status=publish,draft,future&_fields=id,link"); then
  echo "duplicate check failed (request error) — aborting" >&2; exit 1
fi
if ! EXISTING=$(printf '%s' "$LOOKUP" | jq -er 'if type=="array" then (.[0].id // "") else error("not a JSON array") end'); then
  echo "duplicate check failed (unexpected response) — aborting" >&2; exit 1
fi
if [ -n "$EXISTING" ]; then
  echo "already exists as post $EXISTING — update it instead of creating a new one"
  # update:  "${WP[@]}" -X POST "$API/posts/$EXISTING" ...
fi
```

Prefer **updating** the existing post over creating a near-duplicate. This matters
most in Scheduled Tasks, where nobody is watching the output.

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

# Set alt text (image SEO + accessibility) — a separate call on the media object.
jq -n --arg a "Claude API 架构图" '{alt_text:$a}' \
| "${WP[@]}" -X POST "$API/media/$MEDIA_ID" \
    -H "Content-Type: application/json" -d @- | jq '{id, alt_text}'

# Attach as the post's featured image:
#   add  "featured_media": <MEDIA_ID>  to the post body.
```

## Gotchas

- **HTTPS is effectively required for Application Passwords.** WP gates them on
  `wp_is_application_passwords_available()`, which is false on a plain-`http://`
  production site → authenticated calls fail with `rest_not_logged_in` (401). (The
  gate is filterable and is bypassed when `WP_ENVIRONMENT_TYPE` is `local`, so a
  dev box may still work — but any real site the user connects must serve HTTPS.)
- **`$WORDPRESS_SITE_URL` must exactly match the site's configured address.** If
  it differs (missing/extra `www`, `http` vs `https`), WP answers `/wp-json/...`
  with a **301** to the canonical host. Fix the stored site URL in the connector
  rather than papering over it with `-L`.

- **A security plugin / host may block `/wp-json`** (Wordfence, "disable REST
  API" plugins, some managed hosts). Symptom: 404 `rest_no_route` or an HTML
  login page instead of JSON. The user must allow REST API access.
- **Pretty permalinks may be off.** If `/wp-json/wp/v2/...` returns the site's
  HTML instead of JSON, the site is on plain permalinks — use the always-available
  query form instead: `$SITE/?rest_route=/wp/v2/posts`.
- **The Application Password contains spaces** (e.g. `abcd efgh ijkl mnop`).
  Keep them — `curl -u` handles the spaces fine; don't strip them.
- **Never publish silently.** Even if the user says "post it", prefer creating a
  draft and returning the `wp-admin` edit link unless they explicitly asked to
  go live. (In an unattended Scheduled Task the user has pre-authorized the run,
  so publishing directly is expected there — but still run the duplicate check.)


## Record the output

After you successfully publish and obtain the live result URL, call the built-in
`publish_artifact` tool ONCE so the user can track this deliverable in **My Outputs**:

```
publish_artifact(kind="article", channel="wordpress", title="<title>", url="<the REAL returned URL>", status="delivered")
```

Use the real returned URL — never fabricate one. Call it once per published item,
only after delivery is confirmed; skip it (or use `status="failed"`) if publishing failed.
See `_shared/artifacts.md`.
