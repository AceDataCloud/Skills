---
name: figma
description: Read Figma design files, nodes, rendered images and comments via the Figma REST API. Use when the user mentions Figma, a figma.com file link, implementing a design as code, extracting design tokens / colors / spacing, or summarizing comments on a design.
when_to_use: |
  Trigger when the user shares a Figma file URL or wants to read a
  design — get the document tree / a specific frame, render a node to
  PNG/SVG to "see" it, extract styles / tokens, or read comments.
  Read-only. The file key comes from the Figma URL the user pastes.
connections: [figma]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Read **Figma** via `curl + jq`. The user's OAuth bearer token is in
`$FIGMA_TOKEN`; every call needs `Authorization: Bearer $FIGMA_TOKEN`. Base URL:
`https://api.figma.com/v1`.

Failures are `{"status":<code>,"err":"..."}` — show `err` verbatim. `403` means
the token lacks the scope or the file isn't shared with the user. `404` = bad
file key.

The **file key** is the `figma.com/file/<KEY>/...` or `figma.com/design/<KEY>/...`
segment of a pasted URL. A **node id** is in `?node-id=1-23` (Figma shows `1:23`;
the API also accepts `1:23`).

```bash
F="https://api.figma.com/v1"; AUTH=(-H "Authorization: Bearer $FIGMA_TOKEN")
# Who am I (account card)
curl -sS "${AUTH[@]}" "$F/me" | jq '{handle, email}'
# File document tree (name + top-level frames). Big files: prefer /nodes below.
curl -sS "${AUTH[@]}" "$F/files/FILE_KEY?depth=2" \
  | jq '{name, pages: [.document.children[] | {name, frames: [.children[]?.name]}]}'
```

## Read specific nodes & render images

```bash
KEY="FILE_KEY"
# Just the nodes you care about (faster than the whole file)
curl -sS "${AUTH[@]}" "$F/files/$KEY/nodes?ids=1:23,1:45" \
  | jq '.nodes | to_entries[] | {id: .key, name: .value.document.name, type: .value.document.type}'

# Render nodes to images — returns temporary CDN URLs (this is the "see it" tool)
curl -sS "${AUTH[@]}" "$F/images/$KEY?ids=1:23&format=png&scale=2" \
  | jq '.images'   # { "1:23": "https://...png" }
```

For design-to-code, render the frame to PNG (to view) and read its node JSON
(layout/fills/typography) to extract exact colors, spacing and text.

## Comments & projects

```bash
curl -sS "${AUTH[@]}" "$F/files/FILE_KEY/comments" \
  | jq '.comments[] | {user: .user.handle, at: .created_at, message}'
# Team projects → files (needs a team id from the Figma URL /team/<id>/...)
curl -sS "${AUTH[@]}" "$F/teams/TEAM_ID/projects" | jq '.projects'
```

## Gotchas

- Node ids: Figma URLs use `1-23` (dash); the API wants `1:23` (colon). Convert.
- `/images` URLs are **temporary** — download/use them promptly, don't store.
- `depth=` limits tree traversal; omit it only for small files or you'll pull
  megabytes of node JSON.
