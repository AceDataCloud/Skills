---
name: google-drive
description: Read, search, upload, rename, move and delete Google Drive files / folders / shared content via the Drive v3 REST API. Use when the user mentions Drive files, "my drive", shared documents, Google Docs / Sheets / Slides, exporting / downloading a Drive file, searching by name / owner / folder, uploading a new file, renaming or moving files, or organising folders.
when_to_use: |
  Trigger when the user wants to list, search, read, download or
  modify files in their Google Drive — including Google-native docs
  (Docs / Sheets / Slides) which need a special "export" call to get
  plain content, as well as uploads, renames, folder moves, and
  trashing files. The installed connector always grants `drive.readonly`;
  the user opts in to the broader `drive` scope (full read + write)
  at install time — confirm before performing destructive writes.
connections: [google/drive]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.1"
---

Drive Google Drive via `curl + jq`. The user's OAuth bearer token is
in `$GOOGLE_DRIVE_TOKEN`; every call needs it as
`Authorization: Bearer $GOOGLE_DRIVE_TOKEN`. At minimum the token
carries `drive.readonly` plus the identity scopes
(`openid email profile`); if the user opted in to write at install
time it also carries the broader `drive` scope (full read + write).

The Drive API returns standard JSON; failures surface as
`{"error": {"code": 401|403|..., "message": "..."}}` — show that
error verbatim to the user. `401` means the token expired and the
user must re-install the connector. `403 insufficientPermissions`
on a write means the user did not grant the `drive` scope at install
— ask them to re-install with the read+write box checked.

**Before any destructive write** (renaming, moving, trashing, or
bulk-mutating files) show the exact target list and ask the user to
confirm. Never trash by guessing an id — always echo back the file
name + path you're about to touch.

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

## Write recipes

These all need the broader `drive` scope. If the user only granted
`drive.readonly` you'll get `403 insufficientPermissions` — surface
that and suggest re-installing with the read+write box checked.
**Always echo the target name + path back to the user before
trashing or bulk-moving anything.**

### Rename a file

```sh
FILE_ID='1A2B3CdEfGhIjKlMn'
NEW_NAME='2026 Q2 OKR (final).gdoc'
curl -sS -X PATCH -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  -H 'Content-Type: application/json' \
  --data "{\"name\":$(jq -nr --arg n "$NEW_NAME" '$n')}" \
  "https://www.googleapis.com/drive/v3/files/$FILE_ID?fields=id,name"
```

### Move a file to a different folder

Drive's folder model is parent-id based. Move = remove old parent,
add new parent:

```sh
FILE_ID='1A2B3CdEfGhIjKlMn'
NEW_PARENT='1XYZnewFolderId'

# Read existing parents (so we can pass them in removeParents)
OLD_PARENTS=$(curl -sS -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  "https://www.googleapis.com/drive/v3/files/$FILE_ID?fields=parents" \
  | jq -r '.parents | join(",")')

curl -sS -X PATCH -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  --data '' \
  "https://www.googleapis.com/drive/v3/files/$FILE_ID?addParents=$NEW_PARENT&removeParents=$OLD_PARENTS&fields=id,name,parents"
```

### Create a new folder

```sh
PARENT_ID='1XYZparentFolderId'  # or 'root' for My Drive root
curl -sS -X POST -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  -H 'Content-Type: application/json' \
  --data "{\"name\":\"Reports / 2026Q2\",\"mimeType\":\"application/vnd.google-apps.folder\",\"parents\":[\"$PARENT_ID\"]}" \
  "https://www.googleapis.com/drive/v3/files?fields=id,name,webViewLink" \
  | jq
```

### Upload a file (multipart so metadata + bytes go in one request)

```sh
LOCAL=/tmp/report.pdf
NAME='Q2 report.pdf'
PARENT_ID='1XYZparentFolderId'
MIME='application/pdf'

BOUNDARY='aceDataBoundary'
META=$(jq -nc --arg n "$NAME" --arg p "$PARENT_ID" '{name:$n, parents:[$p]}')
{
  printf -- '--%s\r\n' "$BOUNDARY"
  printf 'Content-Type: application/json; charset=UTF-8\r\n\r\n'
  printf '%s\r\n' "$META"
  printf -- '--%s\r\n' "$BOUNDARY"
  printf 'Content-Type: %s\r\n\r\n' "$MIME"
  cat "$LOCAL"
  printf '\r\n--%s--\r\n' "$BOUNDARY"
} > /tmp/_drive_upload.bin

curl -sS -X POST -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  -H "Content-Type: multipart/related; boundary=$BOUNDARY" \
  --data-binary @/tmp/_drive_upload.bin \
  "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink" \
  | jq
```

For a **media-only** upload (no metadata) use `uploadType=media`; for
files >5 MB use `uploadType=resumable` (covered in [Drive's docs]
(https://developers.google.com/drive/api/guides/manage-uploads#resumable)).

### Replace the contents of an existing file

```sh
FILE_ID='1A2B3CdEfGhIjKlMn'
LOCAL=/tmp/report-v2.pdf
curl -sS -X PATCH -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  -H 'Content-Type: application/pdf' \
  --data-binary @"$LOCAL" \
  "https://www.googleapis.com/upload/drive/v3/files/$FILE_ID?uploadType=media&fields=id,name,modifiedTime"
```

Metadata stays the same (id / parents / name) — only the bytes are
replaced and Drive bumps `modifiedTime`.

### Trash a file (or restore one)

```sh
FILE_ID='1A2B3CdEfGhIjKlMn'
curl -sS -X PATCH -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"trashed":true}' \
  "https://www.googleapis.com/drive/v3/files/$FILE_ID?fields=id,name,trashed"

# Restore:
curl -sS -X PATCH -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"trashed":false}' \
  "https://www.googleapis.com/drive/v3/files/$FILE_ID?fields=id,name,trashed"
```

Prefer `trashed:true` over `DELETE` — `DELETE` is permanent and the
user can't undo it. Only use `DELETE` when they explicitly say
"permanently delete".

### Bulk "move every PDF in the root to /Documents/PDF" (confirmation pattern)

```sh
# 1. List candidates and show the user before doing anything
DST_FOLDER_ID='1XYZdocsPdfFolder'
ROOT_ID='root'

CANDS=$(curl -sS -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  --get "https://www.googleapis.com/drive/v3/files" \
  --data-urlencode "q='$ROOT_ID' in parents and mimeType='application/pdf' and trashed=false" \
  --data-urlencode 'fields=files(id,name,webViewLink)' \
  | jq '.files')
echo "$CANDS" | jq -r '.[] | "- \(.name)"'

# 2. (after user confirms) actually move
echo "$CANDS" | jq -r '.[] | .id' | while read FID; do
  curl -sS -X PATCH -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
    --data '' \
    "https://www.googleapis.com/drive/v3/files/$FID?addParents=$DST_FOLDER_ID&removeParents=$ROOT_ID&fields=id,name,parents" \
    | jq -c '{id, name, parents}'
done
```

## Common error codes

| HTTP | meaning | what to tell the user |
|---|---|---|
| `401 UNAUTHENTICATED` | token expired / revoked | "Reconnect the Google Drive connector on the Connections page." |
| `403 insufficientPermissions` | write scope missing | "This action needs the Drive read+write scope, but only `drive.readonly` was granted at install. Re-install the connector and check the read+write box." |
| `403 userRateLimitExceeded` | quota | retry once after 5–10s; if it persists, tell the user. |
| `404 notFound` | wrong file id OR file isn't visible to this account | double-check the id; if shared, use `sharedWithMe` query above. |
| `400 invalidQuery` | malformed `q` | print the `q` you sent + the error message back to the user. |

Never log or echo `$GOOGLE_DRIVE_TOKEN` — treat it as a secret.

Never log or echo `$GOOGLE_DRIVE_TOKEN` — treat it as a secret.
