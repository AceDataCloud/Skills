---
name: hashnode
description: Publish, update and read blog posts on Hashnode via its GraphQL API. Use when the user mentions Hashnode, publishing a blog post to Hashnode, cross-posting an article to their Hashnode blog, saving a Hashnode draft, updating a published Hashnode post, or listing their Hashnode publications and posts.
when_to_use: |
  Trigger when the user wants to publish a Markdown article to their
  Hashnode blog, save it as a draft, update a previously published
  post, or list / inspect their own Hashnode publications and posts.
  The connector stores a Hashnode Personal Access Token with full
  account access — confirm before publishing publicly (you can save a
  draft first with the createDraft mutation).
connections: [hashnode]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Call the **Hashnode Public GraphQL API** with `curl + jq`. The user's Personal
Access Token is in `$HASHNODE_TOKEN`. Single endpoint: `https://gql.hashnode.com`
(always `POST` a JSON body `{query, variables}`).

Every request needs these headers:

```
Authorization: $HASHNODE_TOKEN      # raw token — NO "Bearer " prefix
Content-Type: application/json
```

GraphQL always returns HTTP `200`; real failures live in the JSON `errors`
array — always inspect it and show it verbatim. An `errors` entry mentioning
`Unauthorized` / `not authenticated` means the token is invalid → the user must
re-connect the Hashnode connector.

Helper — send a query/mutation (`$1` = query string, `$2` = variables JSON):

```bash
gql() {
  jq -n --arg q "$1" --argjson v "${2:-null}" '{query:$q, variables:$v}' \
  | curl -sS -X POST https://gql.hashnode.com \
      -H "Authorization: $HASHNODE_TOKEN" \
      -H "Content-Type: application/json" \
      -d @-
}
```

## Always start by confirming the token and finding the publication id

`publishPost` / `createDraft` need a `publicationId`. Fetch the account and its
publications first (a user can have several blogs):

```bash
gql 'query { me { id username publications(first: 10) { edges { node { id title url } } } } }' \
  | jq '{me: .data.me.username, publications: [.data.me.publications.edges[].node | {id, title, url}], errors: .errors}'
```

Pick the target blog's `id` (that is the `publicationId`). If the user has
exactly one publication, use it; otherwise ask which blog to post to.

## Publish a post

**Confirm with the user before publishing publicly.** If they are not sure, save
a draft first (see below). `tags` is required — supply 1–5 tags, each as
`{name, slug}` (slug lowercase, no spaces).

```bash
PUB_ID="PUBLICATION_ID"          # from the me query above
TITLE="My title"
BODY_MD="$(cat article.md)"      # full Markdown body

VARS=$(jq -n --arg p "$PUB_ID" --arg t "$TITLE" --arg b "$BODY_MD" '{
  input: {
    publicationId: $p,
    title: $t,
    contentMarkdown: $b,
    tags: [{name:"AI", slug:"ai"}, {name:"Web Development", slug:"web-development"}]
  }
}')

gql 'mutation PublishPost($input: PublishPostInput!) {
  publishPost(input: $input) { post { id slug url title } }
}' "$VARS" | jq '{post: .data.publishPost.post, errors: .errors}'
```

Useful optional `input` fields:

- `subtitle` — post subtitle.
- `slug` — custom URL slug (otherwise derived from the title).
- `canonicalUrl` / `originalArticleURL` — when cross-posting, point SEO back to
  the original source. Set this whenever the same article also lives elsewhere.
- `coverImageOptions: { coverImageURL: "https://..." }` — cover image.
- `publishedAt` — ISO-8601 timestamp to backdate; `disableComments` etc. live
  under `settings`.

## Save a draft (safe, non-public)

Use this when the user has not explicitly approved public publishing:

```bash
VARS=$(jq -n --arg p "$PUB_ID" --arg t "$TITLE" --arg b "$BODY_MD" '{
  input: { publicationId: $p, title: $t, contentMarkdown: $b }
}')

gql 'mutation CreateDraft($input: CreateDraftInput!) {
  createDraft(input: $input) { draft { id slug title } }
}' "$VARS" | jq '{draft: .data.createDraft.draft, errors: .errors}'
```

## Update a published post

`updatePost` needs the post `id` (from `publishPost`, or the list query below):

```bash
VARS=$(jq -n --arg id "POST_ID" --arg b "$(cat article.md)" '{
  input: { id: $id, contentMarkdown: $b }
}')

gql 'mutation UpdatePost($input: UpdatePostInput!) {
  updatePost(input: $input) { post { id url title } }
}' "$VARS" | jq '{post: .data.updatePost.post, errors: .errors}'
```

## List / inspect my posts

```bash
gql 'query { me { posts(pageSize: 20, page: 1) { nodes { id title slug url views reactionCount responseCount publishedAt } } } }' \
  | jq '[.data.me.posts.nodes[] | {id, title, url, views, reactions: .reactionCount, responses: .responseCount}]'
```

Single post with full content + stats:

```bash
gql 'query GetPost($id: ObjectId!) { post(id: $id) { title url views reactionCount responseCount content { markdown } } }' \
  "$(jq -n --arg id "POST_ID" '{id:$id}')" | jq '.data.post | {title, url, views, reactions: .reactionCount}'
```

## Gotchas

- **No `Bearer` prefix** — the `Authorization` header carries the raw token.
- **`publicationId` is mandatory** for publishing/drafting — never guess it, read
  it from the `me` query.
- **`tags` is required on `publishPost`** — supply at least one `{name, slug}`;
  slug must be lowercase with hyphens (e.g. `machine-learning`).
- **`errors` on HTTP 200** — GraphQL reports failures in the `errors` array, not
  via status codes; always surface them.
- **Idempotency** — re-running `publishPost` creates a *new* post each time; to
  change an existing one use `updatePost` with its `id`.


## Record the output

After you successfully publish and obtain the live result URL, call the built-in
`publish_artifact` tool ONCE so the user can track this deliverable in **My Outputs**:

```
publish_artifact(kind="article", channel="hashnode", title="<title>", url="<the REAL returned URL>", status="delivered")
```

Use the real returned URL — never fabricate one. Call it once per published item,
only after delivery is confirmed; skip it (or use `status="failed"`) if publishing failed.
See `_shared/artifacts.md`.
