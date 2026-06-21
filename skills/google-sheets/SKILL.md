---
name: google-sheets
description: Read and edit Google Sheets via the Sheets v4 REST API. Use when the user mentions Google Sheets, a spreadsheet, cells / ranges / tabs, reading or appending rows, updating values, or creating a new spreadsheet.
when_to_use: |
  Trigger when the user wants to read a range from a Sheet, append or
  update rows, add a tab, or create a spreadsheet. The connector grants
  `spreadsheets.readonly` by default; the user opts in to the broader
  `spreadsheets` scope (read + write) at install — confirm before
  writes. Find the spreadsheet id from a Drive URL or a google-drive
  search.
connections: [google/sheets]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Drive **Google Sheets** via `curl + jq`. The user's OAuth bearer token is in
`$GOOGLE_SHEETS_TOKEN`; every call needs `Authorization: Bearer
$GOOGLE_SHEETS_TOKEN`. Base URL: `https://sheets.googleapis.com/v4/spreadsheets`.
The token carries `spreadsheets.readonly` (+ identity); writes need the broader
`spreadsheets` scope.

Failures are `{"error":{"code","message","status"}}` — show verbatim. `401` =
re-install. `403 PERMISSION_DENIED` on a write = read-only scope → re-connect
with read+write.

The spreadsheet id is the `…/spreadsheets/d/<ID>/edit` segment of the URL.

```bash
S="https://sheets.googleapis.com/v4/spreadsheets"; AUTH=(-H "Authorization: Bearer $GOOGLE_SHEETS_TOKEN")
# Tabs + title
curl -sS "${AUTH[@]}" "$S/SPREADSHEET_ID?fields=properties.title,sheets.properties(title,sheetId)" \
  | jq '{title: .properties.title, tabs: [.sheets[].properties.title]}'
```

## Read / append / update values

```bash
ID="SPREADSHEET_ID"
# Read a range (A1 notation; values are rows of cells)
curl -sS "${AUTH[@]}" "$S/$ID/values/Sheet1!A1:D20" | jq '.values'

# Append rows (confirm first). valueInputOption=USER_ENTERED parses formulas/dates.
curl -sS -X POST "${AUTH[@]}" -H "Content-Type: application/json" \
  -d '{"values":[["2026-06-21","Acme",4200]]}' \
  "$S/$ID/values/Sheet1!A1:append?valueInputOption=USER_ENTERED" | jq '.updates'

# Update a fixed range: PUT /values/{range}?valueInputOption=USER_ENTERED
curl -sS -X PUT "${AUTH[@]}" -H "Content-Type: application/json" \
  -d '{"values":[["done"]]}' \
  "$S/$ID/values/Sheet1!E2?valueInputOption=USER_ENTERED" | jq '.updatedCells'
```

## Create a spreadsheet / add a tab

```bash
# New spreadsheet
curl -sS -X POST "${AUTH[@]}" -H "Content-Type: application/json" \
  -d '{"properties":{"title":"Report 2026"}}' "$S" | jq '{spreadsheetId, spreadsheetUrl}'

# Add a tab via batchUpdate (addSheet request)
curl -sS -X POST "${AUTH[@]}" -H "Content-Type: application/json" \
  -d '{"requests":[{"addSheet":{"properties":{"title":"Q3"}}}]}' \
  "$S/$ID:batchUpdate" | jq '.replies'
```

## Gotchas

- **A1 notation:** `Sheet1!A1:D20`; quote tab names with spaces as `'My Tab'!A1`.
- `valueInputOption=RAW` stores strings as-is; `USER_ENTERED` interprets them like
  the UI (numbers, dates, `=FORMULA`). Pick deliberately.
- `values` is row-major (`[[row1...],[row2...]]`); a missing trailing cell just
  comes back short — don't assume rectangular.
