---
name: devto
description: Publish, update and read articles on DEV (dev.to) via the Forem API v1. Use when the user mentions dev.to / DEV Community, publishing a blog post to dev.to, cross-posting an article, updating a published post, or listing their dev.to articles and stats.
when_to_use: |
  Trigger when the user wants to publish a Markdown article to their
  dev.to account, update a previously published article, or list /
  inspect their own dev.to articles (views, reactions, comments). The
  connector stores a DEV API Key with full account access — confirm
  before publishing publicly (you can publish as a draft with
  published=false first).
connections: [devto]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Call the **Forem API v1** (dev.to) with `curl + jq`. The user's API key is in
`$DEVTO_API_KEY`; every call needs the headers `api-key: $DEVTO_API_KEY` and
`Accept: application/vnd.forem.api-v1+json`. Base URL: `https://dev.to/api`.

Errors come back as JSON with an `error` / `status` field — show them verbatim.
`401` means the API key is invalid → the user must re-connect the DEV connector.

**Always start by confirming the key** and learning the account:

```bash
curl -sS -H "api-key: $DEVTO_API_KEY" -H "Accept: application/vnd.forem.api-v1+json" \
  "https://dev.to/api/users/me" | jq '{username, name}'
```

## Publish an article

**Confirm with the user before publishing publicly.** Default to a draft
(`published:false`) unless they explicitly say publish/now.

```bash
TITLE="My title"
BODY_MD="$(cat article.md)"   # full Markdown body
jq -n --arg t "$TITLE" --arg b "$BODY_MD" \
  '{article:{title:$t, body_markdown:$b, published:false, tags:["ai","webdev"]}}' \
| curl -sS -X POST "https://dev.to/api/articles" \
    -H "api-key: $DEVTO_API_KEY" \
    -H "Accept: application/vnd.forem.api-v1+json" \
    -H "Content-Type: application/json" \
    -d @- \
| jq '{id, url, published}'
```

To publish a draft later (or edit), `PUT /api/articles/{id}` with the same
shape (set `published:true`). Front-matter inside `body_markdown` (a `---`
block) can also carry `title`, `tags`, `series`, `canonical_url`, `cover_image`.

- **Canonical URL:** when cross-posting, set
  `"canonical_url":"https://your-blog/original"` so DEV points SEO back to the
  source — important for the article→video / cross-publishing flow.

## List / inspect my articles

```bash
# My published + draft articles (paginated; per_page max 1000).
curl -sS -H "api-key: $DEVTO_API_KEY" -H "Accept: application/vnd.forem.api-v1+json" \
  "https://dev.to/api/articles/me/all?per_page=30" \
  | jq '.[] | {id, title, published, page_views_count, public_reactions_count, comments_count}'

# A single article's full content + stats.
curl -sS -H "api-key: $DEVTO_API_KEY" -H "Accept: application/vnd.forem.api-v1+json" \
  "https://dev.to/api/articles/ARTICLE_ID" | jq '{title, url, reactions: .public_reactions_count, views: .page_views_count}'
```

## Gotchas

- **Tags:** max 4, lowercase, no spaces (e.g. `webdev`, `machinelearning`).
- **Rate limit:** article create/update is throttled (a few per 30s); space out
  bulk publishes or you'll get `429`.
- `body_markdown` is the source of truth — if you put a `---` front-matter block
  at the top, its fields override the JSON `article` fields.


## Record the output

After you successfully publish and obtain the live result URL, call the built-in
`publish_artifact` tool ONCE so the user can track this deliverable in **My Outputs**:

```
publish_artifact(kind="article", channel="devto", title="<title>", url="<the REAL returned URL>", status="delivered")
```

Use the real returned URL — never fabricate one. Call it once per published item,
only after delivery is confirmed; skip it (or use `status="failed"`) if publishing failed.
See `_shared/artifacts.md`.
