---
name: google-docs
description: Read and edit Google Docs via the Docs v1 REST API. Use when the user mentions a Google Doc, reading a document's text, creating a doc, inserting or replacing text, or exporting a doc's content.
when_to_use: |
  Trigger when the user wants to read a Google Doc's content, create a
  new doc, or insert / replace text in one. The connector grants
  `documents.readonly` by default; the user opts in to `documents`
  (read + write) at install — confirm before edits. Find the doc id
  from a Drive URL or a google-drive search.
connections: [google/docs]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Drive **Google Docs** via `curl + jq`. The user's OAuth bearer token is in
`$GOOGLE_DOCS_TOKEN`; every call needs `Authorization: Bearer
$GOOGLE_DOCS_TOKEN`. Base URL: `https://docs.googleapis.com/v1/documents`. The
token carries `documents.readonly` (+ identity); writes need `documents`.

Failures are `{"error":{"code","message","status"}}` — show verbatim. `401` =
re-install. `403 PERMISSION_DENIED` on a write = read-only scope.

The doc id is the `…/document/d/<ID>/edit` segment of the URL.

```bash
D="https://docs.googleapis.com/v1/documents"; AUTH="Authorization: Bearer $GOOGLE_DOCS_TOKEN"
# Read the document. The body is a tree of structural elements; pull plain text:
curl -sS -H "$AUTH" "$D/DOC_ID" \
  | jq -r '.title, ([.body.content[]?.paragraph?.elements[]?.textRun?.content] | join(""))'
```

## Create & edit

```bash
# Create an empty doc
curl -sS -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"title":"Meeting notes 2026-06-21"}' "$D" | jq '{documentId, title}'

# Insert text at the start (index 1) via batchUpdate (confirm first)
curl -sS -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"requests":[{"insertText":{"location":{"index":1},"text":"Hello\n"}}]}' \
  "$D/DOC_ID:batchUpdate" | jq '.documentId'

# Replace all occurrences of a placeholder
curl -sS -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"requests":[{"replaceAllText":{"containsText":{"text":"{{name}}","matchCase":true},"replaceText":"Alex"}}]}' \
  "$D/DOC_ID:batchUpdate" | jq '.replies'
```

## Gotchas

- The document model is **index-based**: text edits target character indices, and
  every insert shifts later indices — for multiple inserts, apply them
  back-to-front or recompute indices between calls.
- To get clean Markdown/plain text, walk `body.content[].paragraph.elements[]
  .textRun.content` (the jq above). Tables / lists need deeper traversal.
- Creating a doc puts it in the user's Drive root; use the `google-drive` skill to
  move/share it.
