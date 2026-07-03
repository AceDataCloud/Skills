---
name: tencent-docs
description: Create, read, list, search, and manage Tencent Docs (腾讯文档) — online documents, sheets, slides, mind maps, flowcharts, smart tables, and forms — via the Tencent Docs Open API. Use when the user mentions 腾讯文档 / Tencent Docs / docs.qq.com, a docs.qq.com link, or wants to create / read / organize a doc, sheet, slide, mind map, or flowchart in their Tencent Docs space.
when_to_use: |
  Trigger when the user wants to work with their Tencent Docs (腾讯文档) space —
  create a new document / sheet / slide / mind map / flowchart / smart table /
  form, read a doc or sheet's content, list a folder, search files by keyword,
  or rename / move / copy / delete a file. Acts in the user's own Tencent Docs
  account, so destructive or outward-facing writes are gated behind confirmation.
connections: [tencentdocs]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# Tencent Docs (腾讯文档)

Drive the [Tencent Docs Open API](https://docs.qq.com/open/document/app/) with
`curl + jq`. Everything runs **in the user's own Tencent Docs account** — only
files they can access, only the scopes they granted at connect time.

## Auth — three headers (NOT a single Bearer)

The `tencentdocs` BYOC connector injects three env vars; every call sends **all
three** headers:

- `TENCENTDOCS_ACCESS_TOKEN` → `Access-Token` header (OAuth2 access token). **Secret.**
- `TENCENTDOCS_CLIENT_ID` → `Client-Id` header (the developer app's Client ID).
- `TENCENTDOCS_OPEN_ID` → `Open-Id` header (the user id returned with the token).

All endpoints live under `https://docs.qq.com/openapi`. Define a reusable header
set once per session:

```sh
AUTH=(-H "Access-Token: $TENCENTDOCS_ACCESS_TOKEN" \
      -H "Client-Id: $TENCENTDOCS_CLIENT_ID" \
      -H "Open-Id: $TENCENTDOCS_OPEN_ID")
```

Never echo, print, or log `TENCENTDOCS_ACCESS_TOKEN` — it is full account access.

## Response shape & error handling

Every response is `{"ret": 0, "msg": "Succeed", "data": {…}}`. **`ret == 0`
means success**; any non-zero `ret` is an error — surface `msg` to the user.
Always check it:

```sh
resp=$(curl -sS "${AUTH[@]}" … )
echo "$resp" | jq 'if .ret == 0 then .data else error("Tencent Docs \(.ret): \(.msg)") end'
```

Common error codes:

| code | meaning | what to do |
|---|---|---|
| `400006` | access token invalid / expired | tell the user to reconnect 腾讯文档 at <https://auth.acedata.cloud/user/connections> — do **not** loop-retry |
| `400007` | VIP (超级会员) privilege required | the requested capability needs a Tencent Docs 超级会员; tell the user, link <https://docs.qq.com/vip> |
| `400008` | 积分 (credits) insufficient | AI-generation quota is exhausted; tell the user to top up |
| `11607` / `-32603` | bad request params | recheck `fileID` / `type` / body fields against the recipe below |

## Doc types (`type` when creating)

| type | Product | Notes |
|---|---|---|
| `doc` | 在线文档 (Word-style) | classic rich-text document |
| `sheet` | 在线表格 (Excel) | data tables |
| `slide` | 幻灯片 (PPT) | presentations |
| `mind` | 思维导图 | mind map |
| `flowchart` | 流程图 | flowchart |
| `smartsheet` | 智能表格 | structured multi-view table |
| `form` | 收集表 | form / survey |

## Recipes

### Verify auth (always run first)

Cheap sanity check — read the app's OpenAPI usage counter:

```sh
curl -sS "${AUTH[@]}" "https://docs.qq.com/openapi/drive/v2/util/resource-use" \
  | jq 'if .ret == 0 then .data else "ERR \(.ret): \(.msg)" end'
```

If this returns `400006`, the connection is expired — have the user reconnect.

### List a folder (root = `/`)

```sh
curl -sS "${AUTH[@]}" \
  "https://docs.qq.com/openapi/drive/v2/folders/%2F?listType=folder&sortType=browse&asc=0" \
  | jq 'if .ret == 0 then [.data.list[]? | {ID, title, type, url}] else . end'
```

`%2F` is the URL-encoded root folder id. For a sub-folder use its folder id in
the path.

### Search files by keyword

```sh
curl -sS -G "${AUTH[@]}" \
  "https://docs.qq.com/openapi/drive/v2/search" \
  --data-urlencode "searchName=Q1 预算" \
  | jq 'if .ret == 0 then [.data.list[]? | {ID, title, type, url}] else . end'
```

### Read a file's metadata

The `fileID` is the last path segment of a `https://docs.qq.com/doc/<id>` (or
`/sheet/`, `/slide/`, …) URL.

```sh
curl -sS "${AUTH[@]}" \
  "https://docs.qq.com/openapi/drive/v2/files/FILE_ID/metadata" \
  | jq 'if .ret == 0 then .data else . end'
```

### Read an online document's content

```sh
curl -sS "${AUTH[@]}" \
  "https://docs.qq.com/openapi/document/v3/files/FILE_ID/export?exportType=text" \
  | jq 'if .ret == 0 then .data else . end'
```

### Read a sheet's cell range

Get the sheet's `sheetId` list from the metadata first, then read a range
(`A1:D10`):

```sh
curl -sS "${AUTH[@]}" \
  "https://docs.qq.com/openapi/spreadsheet/v2/files/FILE_ID/sheets/SHEET_ID/values?range=A1:D10" \
  | jq 'if .ret == 0 then .data.values else . end'
```

### Create a file

`POST /openapi/drive/v2/files` with form-urlencoded `title` + `type`. Returns the
new file's `ID` and `url`.

```sh
curl -sS -X POST "${AUTH[@]}" \
  "https://docs.qq.com/openapi/drive/v2/files" \
  --data-urlencode "title=会议纪要 2026-07-03" \
  --data-urlencode "type=doc" \
  | jq 'if .ret == 0 then {ID: .data.ID, url: .data.url} else . end'
```

Swap `type=sheet` / `slide` / `mind` / `flowchart` / `smartsheet` / `form` for
other doc types. Pass `--data-urlencode "folderID=<id>"` to create inside a
folder instead of the root.

### Upload an image (for embedding in docs)

```sh
curl -sS -X POST "${AUTH[@]}" \
  "https://docs.qq.com/openapi/resources/v2/images" \
  -F "file=@./cover.png" \
  | jq 'if .ret == 0 then .data else . end'
```

### Rename a file — GATED, confirm first

Show the user the current `title` + `url` and the new title, get an explicit
"yes", then run:

```sh
curl -sS -X PATCH "${AUTH[@]}" \
  "https://docs.qq.com/openapi/drive/v2/files/FILE_ID" \
  --data-urlencode "title=新的标题" \
  | jq 'if .ret == 0 then "renamed" else . end'
```

### Move a file — GATED, confirm first

Show the user the file's current `title` + location and the destination folder,
get an explicit "yes", then run. `folderID=/` moves it back to the root.

```sh
curl -sS -X PATCH "${AUTH[@]}" \
  "https://docs.qq.com/openapi/drive/v2/files/FILE_ID/move" \
  --data-urlencode "folderID=DEST_FOLDER_ID" \
  | jq 'if .ret == 0 then "moved" else . end'
```

### Copy a file

```sh
curl -sS -X POST "${AUTH[@]}" \
  "https://docs.qq.com/openapi/drive/v2/files/FILE_ID/copy" \
  --data-urlencode "title=副本 - 项目计划" \
  | jq 'if .ret == 0 then {ID: .data.ID, url: .data.url} else . end'
```

### Delete a file — GATED, confirm first

Deletion moves the file to the recycle bin but is still destructive. **Show the
user the exact `title` + `url`, get an explicit "yes", then run:**

```sh
curl -sS -X DELETE "${AUTH[@]}" \
  "https://docs.qq.com/openapi/drive/v2/files/FILE_ID" \
  | jq 'if .ret == 0 then "deleted" else . end'
```

## Notes

- **Gate writes.** Rename / move / delete / copy and any share-permission change
  act on the user's real files — confirm the exact target before running.
- **Extract ids from links.** When the user pastes a `docs.qq.com/doc/<id>` (or
  `/sheet/`, `/slide/`, `/mind/`, `/flowchart/`, `/form/`, `/smartsheet/`) URL,
  take the id from the path rather than asking for it.
- **Pagination.** List / search endpoints return a cursor / `next` marker in
  `data`; pass it back to fetch the next page. Stop when the marker is empty.
- **Rate / quota.** Free apps get 20,000 API calls/month (超级会员 20,000/day,
  Plus 40,000/day). AI-generation features additionally consume 积分 and may
  require 超级会员 — a `400007` / `400008` means the account tier / credits, not a
  bug in the request.
- **Full API index.** Beyond the recipes above, the Open API also covers
  smart-table records, form collection, folder CRUD, permissions, and
  import/export — see the [接口索引](https://docs.qq.com/open/document/app/openapi/v2/file/).
