---
name: ghost
description: Create drafts and publish or update posts on a self-hosted Ghost site through the official Admin API. Use when the user mentions Ghost, a Ghost publication, newsletters, or publishing an article to their own Ghost site.
when_to_use: |
  Trigger when the user wants to list, create, update, draft, or publish posts
  on a self-hosted Ghost site. Public writes require explicit confirmation.
connections: [ghost]
allowed_tools: [Bash, publish_artifact]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# Ghost Admin API

Use the bundled standard-library client. The connector injects:

- `$GHOST_SITE_URL` — site root, such as `https://blog.example.com`
- `$GHOST_ADMIN_API_KEY` — Ghost custom integration key (`id:hexsecret`)

The key grants administrative publishing access. Never print, log, or place it
in command arguments.

```bash
G="$SKILL_DIR/scripts/ghost.py"
[ -f "$G" ] || G=$(find /tmp -maxdepth 8 -path '*/skills/*/ghost/scripts/ghost.py' 2>/dev/null | head -1)
[ -f "$G" ] || { echo "ghost script not found" >&2; exit 1; }

python3 "$G" posts --limit 10
```

## Create a private draft

```bash
python3 "$G" create --title "Title" --html-file article.html --status draft --confirm
```

Ghost's Admin API accepts HTML through `?source=html`. Convert Markdown to HTML
first. `create` is a dry run unless the trailing argument is `--confirm`.

## Publish

```bash
python3 "$G" create --title "Title" --html-file article.html --status published
python3 "$G" create --title "Title" --html-file article.html --status published --confirm
```

The first command only prints the proposed operation. Before the confirmed call,
show the final title and body and obtain explicit approval. Use the returned
`.posts[0].url`; never construct or guess a URL.

## Update an existing post

Ghost requires the current `updated_at` value for conflict detection:

```bash
python3 "$G" update --id POST_ID --updated-at "2026-07-21T12:00:00.000Z" \
  --title "Revised title" --html-file revised.html
python3 "$G" update --id POST_ID --updated-at "2026-07-21T12:00:00.000Z" \
  --title "Revised title" --html-file revised.html --confirm
```

## Errors

| HTTP | Meaning | Action |
|---|---|---|
| 401 | Invalid/revoked Admin API key | Reconnect Ghost with a current custom-integration key |
| 403 | Integration lacks access | Check the integration and site permissions |
| 409 | Stale `updated_at` | Re-read the post, review changes, and retry with its latest timestamp |
| 422 | Invalid post payload | Surface Ghost's validation message and fix the content |

If a confirmed create/update ends with a network error, the result is unknown:
do not repeat the write. Run `posts`, compare title/status/updated time, and only
retry after proving Ghost did not accept the original request.

After a confirmed publish returns a real URL, record it once with
`publish_artifact(kind="article", channel="ghost", ...)`.
