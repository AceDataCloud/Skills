---
name: google-drive
description: Read, export, upload, rename, move and delete Google Drive files explicitly selected or shared with the app via the Drive v3 REST API. Use when the user provides a Drive file ID/link or has selected files for the Google Drive connector.
when_to_use: |
  Trigger when the user wants to read, download, export or modify Google
  Drive files they explicitly selected, created, opened, or shared with
  this app. The installed connector currently grants only `drive.file`,
  so do not browse, search, or summarize the user's entire Drive.
connections: [google/drive]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.2"
---

Drive Google Drive via `curl + jq`. The user's OAuth bearer token is
in `$GOOGLE_DRIVE_TOKEN`; every call needs it as
`Authorization: Bearer $GOOGLE_DRIVE_TOKEN`. The token carries
`drive.file` plus identity scopes (`openid email profile`) and can only
access files the user selected, opened, created, or shared with this app.

The Drive API returns standard JSON; failures surface as
`{"error": {"code": 401|403|..., "message": "..."}}` — show that
error verbatim to the user. `401` means the token expired and the
user must re-install the connector. `403 insufficientPermissions`
means the file was not shared with this app, or the action needs a
broader Drive scope that is temporarily disabled during Google review.

Do not use this skill for broad Drive discovery: no "list my recent
files", full-text search across Drive, shared-with-me scans, root-folder
cleanup, or bulk moves based on a Drive-wide query. Ask the user to pick
or paste the exact file/folder IDs first.

**Before any destructive write** (renaming, moving, trashing, or
bulk-mutating files) show the exact target list and ask the user to
confirm. Never trash by guessing an id — always echo back the file
name + path you're about to touch.

**Always start with `/about?fields=user`** to confirm the connection
works AND learn which Google account you're operating against.

## Optional: Google Workspace CLI (`gws`) for uploads

[`gws`](https://github.com/googleworkspace/cli) is Google's official CLI
(not officially supported — community-maintained on the `googleworkspace`
org). It dynamically builds its command surface from Google's Discovery
Document, exits non-zero on API errors, supports `--page-all`
auto-pagination, and ships a `+upload` helper that wraps the multipart
upload protocol.

**Use `gws` for uploads.** A Drive multipart upload requires a
hand-formatted `multipart/related` body with a JSON metadata part and a
binary file part separated by a boundary string — easy to get wrong from
curl. `gws drive +upload` does it correctly. **For everything else**
(get, export, rename, move, trash, delete) the curl recipes below are
equivalent and shorter — stay on those.

### Install

```sh
npm install -g @googleworkspace/cli   # or: brew install googleworkspace-cli
# Pre-built binaries also at https://github.com/googleworkspace/cli/releases
gws --version
```

### Auth

`gws` reads its OAuth bearer token from the `GOOGLE_WORKSPACE_CLI_TOKEN`
environment variable. The Drive token used in this skill is in
`$GOOGLE_DRIVE_TOKEN`, so re-export it once at the top of every shell
block that calls `gws`:

```sh
export GOOGLE_WORKSPACE_CLI_TOKEN="$GOOGLE_DRIVE_TOKEN"
```

### Upload

```sh
# Simple upload to My Drive (auto-detects MIME type, sets the file name
# from --name; falls back to the local filename if --name is omitted)
gws drive +upload ./report.pdf --name "Q1 Report"

# Upload into a specific folder, or with explicit metadata, via the
# generic Discovery method + --upload (multipart wire format handled
# for you)
gws drive files create \
  --json '{"name":"report.pdf","parents":["FOLDER_ID"],"description":"Q1"}' \
  --upload ./report.pdf
```

Both exit non-zero with a structured JSON error on stderr if Google
rejects the request — surface that verbatim.

## Recipes

### Verify auth (always run first)

```sh
curl -sS -H "Authorization: Bearer $GOOGLE_DRIVE_TOKEN" \
  "https://www.googleapis.com/drive/v3/about?fields=user(displayName,emailAddress,photoLink),storageQuota(usage,limit)" \
  | jq '{user, quota: .storageQuota}'
```

### List children of a selected folder

Only use this after the user explicitly selected or provided the folder ID.

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

## Write recipes

These only work for files and folders available through `drive.file`.
If Google returns `403 insufficientPermissions`, surface the error and
ask the user to select/share the target file with the app.
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

## Common error codes

| HTTP | meaning | what to tell the user |
|---|---|---|
| `401 UNAUTHENTICATED` | token expired / revoked | "Reconnect the Google Drive connector on the Connections page." |
| `403 insufficientPermissions` | target not shared with app / broader Drive scope disabled | "This file isn't available to the app under the current `drive.file` permission. Select or share the exact file with the Google Drive connector, then try again." |
| `403 userRateLimitExceeded` | quota | retry once after 5–10s; if it persists, tell the user. |
| `404 notFound` | wrong file id OR file isn't visible to this app | double-check the id; ask the user to select or share the file with the connector. |
| `400 invalidQuery` | malformed `q` | print the `q` you sent + the error message back to the user. |

Never log or echo `$GOOGLE_DRIVE_TOKEN` — treat it as a secret.
