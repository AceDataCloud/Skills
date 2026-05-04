---
name: notion
description: Search, read, append to, and create Notion pages and databases via the Notion REST API. Use when the user mentions Notion, a page in their workspace, or wants to log something to a database.
when_to_use: |
  Trigger when the user wants to read or write something in Notion —
  search a workspace, read a page, append blocks, query a database,
  create a page from a template, etc.
connections: [notion]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

We drive the [Notion API](https://developers.notion.com/reference) with
`curl + jq`. The user's OAuth bearer token is in `$NOTION_TOKEN`; every
call needs it plus the `Notion-Version` header.

Notion-Version is currently `2022-06-28` (the most recent stable). Bump
this header when Notion ships a new version.

The user's connection only sees the pages and databases they explicitly
shared with the integration when they authorized. If a search or page
read returns nothing, the most likely cause is "the page was never
shared with the integration" — surface that hint to the user.

## Recipes

### Verify auth (always run first)

```sh
curl -sS https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  | jq '{id, name, type, bot: (.bot != null)}'
```

### Search the workspace

```sh
curl -sS https://api.notion.com/v1/search \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{"query": "Q1 budget", "page_size": 10}' \
  | jq '.results[] | {id, type: .object, url, title: (.properties.title // .properties.Name)?.title?[0]?.plain_text // .child_page?.title}'
```

### Read a page (metadata only)

```sh
curl -sS "https://api.notion.com/v1/pages/PAGE_ID" \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28"
```

### Read a page's full content

```sh
curl -sS "https://api.notion.com/v1/blocks/PAGE_ID/children?page_size=100" \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  | jq '.results[] | {type, content: (.[.type] // {})}'
```

### Append a paragraph to a page

```sh
curl -sS -X PATCH "https://api.notion.com/v1/blocks/PAGE_ID/children" \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d "$(jq -nc --arg text "Appended via the assistant." '
    {children: [{
      object: "block",
      type: "paragraph",
      paragraph: {rich_text: [{type:"text", text:{content:$text}}]}
    }]}')"
```

### Query a database

```sh
curl -sS -X POST "https://api.notion.com/v1/databases/DATABASE_ID/query" \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {"property": "Status", "select": {"equals": "Open"}},
    "sorts":  [{"property": "Updated", "direction": "descending"}],
    "page_size": 25
  }'
```

### Create a page in a database

```sh
curl -sS -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d "$(jq -nc \
        --arg db "DATABASE_ID" \
        --arg title "New entry" \
        '{
          parent: {database_id: $db},
          properties: {
            Name:   {title: [{text: {content: $title}}]},
            Status: {select: {name: "Open"}}
          }
        }')"
```

## Notes

- Notion's pagination is cursor-based: append `start_cursor=$cursor` to
  paginate, using the `next_cursor` from each response. Stop when
  `has_more` is `false`.
- Most write failures (400/404) come from a property type mismatch —
  e.g. sending `{"select": "Open"}` instead of `{"select": {"name": "Open"}}`.
  Read the database schema once via `GET /v1/databases/<id>` if unsure.
