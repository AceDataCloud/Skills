---
name: feishu
description: Read and write Feishu (飞书) docs, sheets, Base (bitable), Drive files, calendar events, tasks, wiki, and IM messages via the Feishu Open Platform REST API. Use when the user mentions 飞书 / Feishu / Lark, a Feishu document or sheet link, their Feishu calendar, or wants to send a Feishu message.
when_to_use: |
  Trigger when the user wants to read or write something in Feishu (飞书) —
  summarize / create / edit a doc, read or append to a spreadsheet, query
  or add Base (bitable) records, browse Drive files, look at or create
  calendar events, manage tasks, read wiki nodes, or send an IM message.
connections: [feishu]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

We drive the [Feishu Open Platform API](https://open.feishu.cn/document)
with `curl + jq`. The user's OAuth `user_access_token` is in
`$FEISHU_TOKEN`; every call sends it as `Authorization: Bearer
$FEISHU_TOKEN`. All endpoints live under `https://open.feishu.cn/open-apis`.

Calls run **in the user's context** (their docs, calendar, messages) — only
data the user can access and only the scopes they granted at connect time
(docs / sheets / base / drive / calendar / IM / wiki / task / contacts).

## Response shape & error handling

Every Feishu response is `{"code": 0, "msg": "success", "data": {…}}`.
**`code == 0` means success**; any non-zero `code` is an error — surface
`msg` to the user. Always check it:

```sh
resp=$(curl -sS … )
echo "$resp" | jq 'if .code == 0 then .data else error("Feishu \(.code): \(.msg)") end'
```

Common error codes:

| code | meaning | what to do |
|---|---|---|
| `99991663` / `99991668` | access token invalid / expired | tell the user to reconnect Feishu in 连接 settings |
| `99991661` | no permission (scope not granted) | the connect-time scope is missing — reconnect and grant it |
| `1254xxx` | resource not found / no access | the user can't see that doc / sheet / app — double-check the token/id |

## Recipes

### Verify auth (always run first)

```sh
curl -sS https://open.feishu.cn/open-apis/authen/v1/user_info \
  -H "Authorization: Bearer $FEISHU_TOKEN" \
  | jq 'if .code == 0 then {name: .data.name, open_id: .data.open_id, email: .data.email} else . end'
```

### Docs (docx)

A Feishu doc URL looks like `https://…feishu.cn/docx/<document_id>`. The
`document_id` is the last path segment.

Read a document's plain text:

```sh
curl -sS "https://open.feishu.cn/open-apis/docx/v1/documents/DOCUMENT_ID/raw_content" \
  -H "Authorization: Bearer $FEISHU_TOKEN" \
  | jq -r 'if .code == 0 then .data.content else "ERR \(.code): \(.msg)" end'
```

List a document's blocks (structured content):

```sh
curl -sS "https://open.feishu.cn/open-apis/docx/v1/documents/DOCUMENT_ID/blocks?page_size=500" \
  -H "Authorization: Bearer $FEISHU_TOKEN" \
  | jq 'if .code == 0 then [.data.items[] | {block_id, block_type}] else . end'
```

Create a new empty document (optionally inside a folder):

```sh
curl -sS -X POST "https://open.feishu.cn/open-apis/docx/v1/documents" \
  -H "Authorization: Bearer $FEISHU_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(jq -nc --arg title "会议纪要 2026-07-01" '{title: $title}')" \
  | jq 'if .code == 0 then {document_id: .data.document.document_id} else . end'
```

Append a text block to a document (insert at the end of the document body —
`DOCUMENT_ID` is also the root block id):

```sh
curl -sS -X POST "https://open.feishu.cn/open-apis/docx/v1/documents/DOCUMENT_ID/blocks/DOCUMENT_ID/children" \
  -H "Authorization: Bearer $FEISHU_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(jq -nc --arg text "由助手追加的一段内容。" '
    {children: [{block_type: 2, text: {elements: [{text_run: {content: $text}}]}}]}')" \
  | jq 'if .code == 0 then "appended" else . end'
```

### Spreadsheets (sheets v2)

A sheet URL looks like `https://…feishu.cn/sheets/<spreadsheet_token>`.
A range is `<sheetId>!<A1:range>`, e.g. `abc123!A1:D10`. List sheet ids via
the metainfo endpoint first if you don't have one.

Read a range:

```sh
curl -sS "https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/SPREADSHEET_TOKEN/values/RANGE" \
  -H "Authorization: Bearer $FEISHU_TOKEN" \
  | jq 'if .code == 0 then .data.valueRange.values else . end'
```

Append rows after the last non-empty row:

```sh
curl -sS -X POST "https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/SPREADSHEET_TOKEN/values_append" \
  -H "Authorization: Bearer $FEISHU_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(jq -nc '{valueRange: {range: "SHEET_ID!A1:B1", values: [["张三", 100], ["李四", 200]]}}')" \
  | jq 'if .code == 0 then .data.updates else . end'
```

### Base / 多维表格 (bitable v1)

A Base URL looks like `https://…feishu.cn/base/<app_token>`. Get `table_id`
from `…/bitable/v1/apps/APP_TOKEN/tables`.

List records:

```sh
curl -sS "https://open.feishu.cn/open-apis/bitable/v1/apps/APP_TOKEN/tables/TABLE_ID/records?page_size=100" \
  -H "Authorization: Bearer $FEISHU_TOKEN" \
  | jq 'if .code == 0 then [.data.items[] | {record_id, fields}] else . end'
```

Create a record:

```sh
curl -sS -X POST "https://open.feishu.cn/open-apis/bitable/v1/apps/APP_TOKEN/tables/TABLE_ID/records" \
  -H "Authorization: Bearer $FEISHU_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(jq -nc '{fields: {"标题": "新任务", "状态": "待办"}}')" \
  | jq 'if .code == 0 then {record_id: .data.record.record_id} else . end'
```

### Drive files

List files in a folder (omit `folder_token` for the root):

```sh
curl -sS "https://open.feishu.cn/open-apis/drive/v1/files?folder_token=FOLDER_TOKEN&page_size=50" \
  -H "Authorization: Bearer $FEISHU_TOKEN" \
  | jq 'if .code == 0 then [.data.files[] | {name, type, token, url}] else . end'
```

### Calendar (v4)

List the user's calendars (the primary one has `type: "primary"`):

```sh
curl -sS "https://open.feishu.cn/open-apis/calendar/v4/calendars?page_size=50" \
  -H "Authorization: Bearer $FEISHU_TOKEN" \
  | jq 'if .code == 0 then [.data.calendar_list[] | {calendar_id, summary, type}] else . end'
```

List events in a time window (epoch-seconds strings):

```sh
curl -sS "https://open.feishu.cn/open-apis/calendar/v4/calendars/CALENDAR_ID/events?start_time=1751299200&end_time=1751385600&page_size=100" \
  -H "Authorization: Bearer $FEISHU_TOKEN" \
  | jq 'if .code == 0 then [.data.items[] | {summary, start: .start_time, end: .end_time, event_id}] else . end'
```

Create an event (times are epoch-seconds strings):

```sh
curl -sS -X POST "https://open.feishu.cn/open-apis/calendar/v4/calendars/CALENDAR_ID/events" \
  -H "Authorization: Bearer $FEISHU_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(jq -nc '{summary: "项目评审", start_time: {timestamp: "1751302800"}, end_time: {timestamp: "1751306400"}}')" \
  | jq 'if .code == 0 then {event_id: .data.event.event_id} else . end'
```

### Tasks (v2)

List the user's tasks:

```sh
curl -sS "https://open.feishu.cn/open-apis/task/v2/tasks?page_size=50" \
  -H "Authorization: Bearer $FEISHU_TOKEN" \
  | jq 'if .code == 0 then [.data.items[] | {summary, completed_at, task_guid: .guid}] else . end'
```

Create a task:

```sh
curl -sS -X POST "https://open.feishu.cn/open-apis/task/v2/tasks" \
  -H "Authorization: Bearer $FEISHU_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(jq -nc '{summary: "准备周会材料"}')" \
  | jq 'if .code == 0 then {task_guid: .data.task.guid} else . end'
```

### Wiki

List wiki spaces, then nodes within a space:

```sh
curl -sS "https://open.feishu.cn/open-apis/wiki/v2/spaces?page_size=50" \
  -H "Authorization: Bearer $FEISHU_TOKEN" \
  | jq 'if .code == 0 then [.data.items[] | {space_id, name}] else . end'

curl -sS "https://open.feishu.cn/open-apis/wiki/v2/spaces/SPACE_ID/nodes?page_size=50" \
  -H "Authorization: Bearer $FEISHU_TOKEN" \
  | jq 'if .code == 0 then [.data.items[] | {title, node_token, obj_type}] else . end'
```

### Send an IM message

Send to a user by `open_id` (use `receive_id_type=chat_id` for a group
chat). `content` must be a JSON **string**, so it's double-encoded:

```sh
curl -sS -X POST "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id" \
  -H "Authorization: Bearer $FEISHU_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(jq -nc --arg rid "ou_xxx" --arg text "你好，这是助手发送的消息。" '
    {receive_id: $rid, msg_type: "text", content: ({text: $text} | tostring)}')" \
  | jq 'if .code == 0 then {message_id: .data.message_id} else . end'
```

## Notes

- Confirm destructive or outward-facing actions (sending a message,
  creating a calendar invite, posting to a shared doc) with the user
  before running them.
- Pagination: list endpoints return `data.page_token` / `data.has_more`;
  pass `page_token=…` to fetch the next page.
- When the user pastes a Feishu link, extract the token/id from the URL
  path rather than asking them for it.
