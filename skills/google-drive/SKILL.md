---
name: google-drive
description: Read and search Google Drive files / folders / shared content via the Drive v3 REST API. Use when the user mentions Drive files, "my drive", shared documents, Google Docs / Sheets / Slides, exporting / downloading a Drive file, or searching by name / owner / folder.
when_to_use: |
  Trigger when the user wants to list, search, read or download files
  in their Google Drive — including Google-native docs (Docs / Sheets /
  Slides) which need a special "export" call to get plain content. The
  installed connector grants read-only scope (`drive.readonly`); writes
  are out of scope.
connections: [google/drive]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Drive Google Drive via `curl + jq`. The user's OAuth bearer token is
in `$GOOGLE_DRIVE_TOKEN`; every call needs it as
`Authorization: Bearer $GOOGLE_DRIVE_TOKEN`. The token already carries
the `drive.readonly` scope the user agreed to at install plus the
identity scopes (`openid email profile`).

The Drive API returns standard JSON; failures surface as
`{"error": {"code": 401|403|..., "message": "..."}}` — show that
error verbatim to the user. `401` means the token expired and the
user must re-install the connector. `403 insufficientPermissions`
means the connector grants only `drive.readonly` and the user is
asking for a write — say so explicitly.

**Always start with `/about?fields=user`** to confirm the connection
works AND learn which Google account you're operating against.

## Recipes

### Verify auth (always run first)

```sh
curl -sS -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  "https://www.googleapis.com/drive/v3/about?fields=user(displayName,emailAddress,photoLink),storageQuota(usage,limit)" \
  | jq '{user, quota: .storageQuota}'
```

### List recent files (last modified first)

```sh
curl -sS -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  "https://www.googleapis.com/drive/v3/files?orderBy=modifiedTime%20desc&pageSize=20&fields=files(id,name,mimeType,modifiedTime,owners(emailAddress),webViewLink,parents)" \
  | jq '.files[] | {id, name, mimeType, modified: .modifiedTime, owner: .owners[0].emailAddress, webViewLink}'
```

`pageSize` max is 1000; default is 100. Use `pageToken` from the
response (`nextPageToken`) for follow-up pages.

### Search by name / fulltext

```sh
# Exact-name fragments — note "name contains" supports tokens, not regex
Q='name contains "季度复盘" and trashed = false'
curl -sS -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  --get "https://www.googleapis.com/drive/v3/files" \
  --data-urlencode "q=$Q" \
  --data-urlencode 'fields=files(id,name,mimeType,modifiedTime,webViewLink,owners(emailAddress))' \
  --data-urlencode 'pageSize=20' \
  | jq '.files[] | {id, name, modified: .modifiedTime, owner: .owners[0].emailAddress}'

# Full-text search (body + title)
Q='fullText contains "OKR 2026Q2" and trashed = false'
curl -sS -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  --get "https://www.googleapis.com/drive/v3/files" \
  --data-urlencode "q=$Q" \
  --data-urlencode 'fields=files(id,name,modifiedTime,webViewLink)' \
  | jq '.files[]'
```

The `q` param uses [Drive's mini query language](https://developers.google.com/drive/api/guides/search-files):
`name`, `fullText`, `mimeType`, `parents`, `'<email>' in owners`,
`'<email>' in writers`, `modifiedTime > '2026-01-01T00:00:00'`,
`sharedWithMe`, `trashed`, joined by `and` / `or` / `not`.

### List files shared with me

```sh
curl -sS -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  --get "https://www.googleapis.com/drive/v3/files" \
  --data-urlencode 'q=sharedWithMe and trashed = false' \
  --data-urlencode 'orderBy=sharedWithMeTime desc' \
  --data-urlencode 'fields=files(id,name,mimeType,sharedWithMeTime,owners(displayName,emailAddress))' \
  --data-urlencode 'pageSize=30' \
  | jq '.files[] | {name, sharedAt: .sharedWithMeTime, sharedBy: .owners[0]}'
```

### List children of a folder

```sh
FOLDER_ID='1A2B3CdEfGhIjKlMn'
curl -sS -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  --get "https://www.googleapis.com/drive/v3/files" \
  --data-urlencode "q='$FOLDER_ID' in parents and trashed = false" \
  --data-urlencode 'fields=files(id,name,mimeType,size,modifiedTime),nextPageToken' \
  | jq '.files'
```

### Get metadata for a single file

```sh
FILE_ID='1A2B3CdEfGhIjKlMn'
curl -sS -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  "https://www.googleapis.com/drive/v3/files/$FILE_ID?fields=id,name,mimeType,size,modifiedTime,parents,owners,webViewLink,description"
```

### Download a binary file (PDF / image / zip / …)

```sh
FILE_ID='1A2B3CdEfGhIjKlMn'
OUT=/tmp/download.bin
curl -sS -L -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  "https://www.googleapis.com/drive/v3/files/$FILE_ID?alt=media" \
  -o "$OUT"
file "$OUT" && wc -c "$OUT"
```

### Read a Google Doc as plain markdown / text

Google-native files (Docs, Sheets, Slides) **don't have raw bytes** —
you have to ask Drive to *export* them to a concrete MIME type:

```sh
DOC_ID='1A2B3CdEfGhIjKlMn'

# Markdown (best for chat-friendly summaries)
curl -sS -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  "https://www.googleapis.com/drive/v3/files/$DOC_ID/export?mimeType=text/markdown" \
  > /tmp/doc.md
head -40 /tmp/doc.md

# Plain text fallback for older docs
curl -sS -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  "https://www.googleapis.com/drive/v3/files/$DOC_ID/export?mimeType=text/plain" \
  > /tmp/doc.txt
```

Common export MIME types:

| native MIME | export to |
|---|---|
| `application/vnd.google-apps.document` | `text/markdown`, `text/plain`, `text/html`, `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `application/vnd.google-apps.spreadsheet` | `text/csv`, `application/pdf`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `application/vnd.google-apps.presentation` | `application/pdf`, `text/plain`, `application/vnd.openxmlformats-officedocument.presentationml.presentation` |

### Read a Google Sheet as CSV

```sh
SHEET_ID='1A2B3CdEfGhIjKlMn'
curl -sS -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  "https://www.googleapis.com/drive/v3/files/$SHEET_ID/export?mimeType=text/csv" \
  > /tmp/sheet.csv
head /tmp/sheet.csv
```

The Drive `export` endpoint returns the **first sheet only**. For
multi-tab access the user needs to install a separate Google Sheets
connector (currently out of catalog) — explain that and stop.

### Get permissions / sharing on a file

```sh
FILE_ID='1A2B3CdEfGhIjKlMn'
curl -sS -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  "https://www.googleapis.com/drive/v3/files/$FILE_ID/permissions?fields=permissions(id,type,role,emailAddress,domain,deleted)" \
  | jq '.permissions[] | {who: (.emailAddress // .domain // .type), role}'
```

### Pagination boilerplate

```sh
PAGE_TOKEN=''
while : ; do
  RESP=$(curl -sS -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
    --get "https://www.googleapis.com/drive/v3/files" \
    --data-urlencode 'q=trashed = false' \
    --data-urlencode 'fields=files(id,name),nextPageToken' \
    --data-urlencode 'pageSize=200' \
    ${PAGE_TOKEN:+--data-urlencode "pageToken=$PAGE_TOKEN"})
  echo "$RESP" | jq -c '.files[]'
  PAGE_TOKEN=$(echo "$RESP" | jq -r '.nextPageToken // empty')
  [ -z "$PAGE_TOKEN" ] && break
done
```

## Common error codes

| HTTP | meaning | what to tell the user |
|---|---|---|
| `401 UNAUTHENTICATED` | token expired / revoked | "Reconnect the Google Drive connector on the Connections page." |
| `403 insufficientPermissions` | scope missing | "Your installed connector only grants read access — this action needs a write scope we don't have." |
| `403 userRateLimitExceeded` | quota | retry once after 5–10s; if it persists, tell the user. |
| `404 notFound` | wrong file id OR file isn't visible to this account | double-check the id; if shared, use `sharedWithMe` query above. |
| `400 invalidQuery` | malformed `q` | print the `q` you sent + the error message back to the user. |

Never log or echo `$GOOGLE_DRIVE_TOKEN` — treat it as a secret.
