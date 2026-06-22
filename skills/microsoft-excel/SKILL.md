---
name: microsoft-excel
description: Read and edit live Excel workbooks stored in OneDrive / SharePoint via the Microsoft Graph workbook API. Use when the user mentions an Excel file, a spreadsheet on OneDrive, reading a range or table, appending rows, updating cells, or listing worksheets in a cloud .xlsx.
when_to_use: |
  Trigger when the user wants to read or write a cloud Excel workbook
  (one that lives in their OneDrive / SharePoint) — read a used range,
  read/update cells, add rows to a table, list worksheets. The
  connector grants `Files.ReadWrite` (or `Files.Read` read-only). Find
  the file id first via OneDrive search; confirm before writes.
connections: [microsoft/excel]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Drive **live Excel workbooks** via the Microsoft Graph workbook API with
`curl + jq`. The user's OAuth bearer token is in `$MICROSOFT_EXCEL_TOKEN`; every
call needs `Authorization: Bearer $MICROSOFT_EXCEL_TOKEN`. Base URL:
`https://graph.microsoft.com/v1.0`. The workbook API operates on a **drive item**
(an .xlsx in OneDrive/SharePoint), so you need its `ITEM_ID`.

Failures are `{"error":{"code","message"}}` — show `message` verbatim. `401` =
token expired (re-install). `403` on a write = the user granted read-only.

```bash
G="https://graph.microsoft.com/v1.0"; AUTH="Authorization: Bearer $MICROSOFT_EXCEL_TOKEN"
# Find the workbook by name (then take .id as ITEM_ID)
curl -sS -H "$AUTH" "$G/me/drive/root/search(q='budget.xlsx')" \
  | jq '.value[] | {id, name, webUrl}'
# Worksheets in the workbook
curl -sS -H "$AUTH" "$G/me/drive/items/ITEM_ID/workbook/worksheets" \
  | jq '.value[] | {id, name, position}'
```

## Read & write ranges

```bash
ITEM="ITEM_ID"; WS="Sheet1"
# Used range (values + formulas + formats)
curl -sS -H "$AUTH" \
  "$G/me/drive/items/$ITEM/workbook/worksheets/$WS/usedRange" \
  | jq '{address, values: .values}'

# Read a specific range
curl -sS -H "$AUTH" \
  "$G/me/drive/items/$ITEM/workbook/worksheets/$WS/range(address='A1:C5')" | jq '.values'

# Update a range (confirm first). values is a 2-D array matching the address shape.
curl -sS -X PATCH -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"values":[["Q3",1200],["Q4",1580]]}' \
  "$G/me/drive/items/$ITEM/workbook/worksheets/$WS/range(address='A2:B3')" | jq '.address'
```

## Append a row to a table

```bash
curl -sS -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"values":[["2026-06-21","Acme",4200]]}' \
  "$G/me/drive/items/$ITEM/workbook/tables/Table1/rows/add" | jq '.index'
```

## Gotchas

- This is for **cloud** workbooks (OneDrive/SharePoint). A local .xlsx the user
  uploaded into chat is a different job (parse the file directly), not this skill.
- Range `address` is a string like `Sheet1!A1:C5` or just `A1:C5` when scoped to a
  worksheet; `values` must be a 2-D array matching its dimensions.
- For long-running edits Graph supports a **workbook session** header
  (`workbook-session-id`); for a few cells the default sessionless mode is fine.
