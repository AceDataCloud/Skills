---
name: microsoft-onedrive
description: Read and manage OneDrive / SharePoint files via Microsoft Graph. Use when the user mentions OneDrive files / folders, SharePoint documents, file uploads / downloads, sharing links, or "my drive".
when_to_use: |
  Trigger when the user wants to read, list, search, upload, download,
  rename, move, share or delete files in OneDrive (personal or
  Microsoft 365 work / school) or SharePoint document libraries.
connections: [microsoft/onedrive]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Drive Microsoft Graph for OneDrive / SharePoint via `curl + jq`. The
user's OAuth bearer token is in `$MICROSOFT_ONEDRIVE_TOKEN`; every call
needs it as `Authorization: Bearer $MICROSOFT_ONEDRIVE_TOKEN`. The token
already carries the OneDrive scopes the user agreed to at install time
(`Files.Read`, `Files.Read.All`, optionally `Files.ReadWrite.All`,
`Sites.Read.All`).

The Graph API returns standard JSON; failures surface as JSON
`{"error": {"code": "...", "message": "..."}}` — show that error
verbatim to the user.

**Always start with `/me`** to confirm the connection works AND learn
which account / drive you're operating against.

## Recipes

### Verify auth (always run first)

```sh
curl -sS -H "Authorization: Bearer $MICROSOFT_ONEDRIVE_TOKEN" \
  https://graph.microsoft.com/v1.0/me \
  | jq '{displayName, mail, userPrincipalName}'
```

If you get `401 InvalidAuthenticationToken`, the token expired —
report it; the user has to reinstall the connector.

### List files in root

```sh
curl -sS -H "Authorization: Bearer $MICROSOFT_ONEDRIVE_TOKEN" \
  "https://graph.microsoft.com/v1.0/me/drive/root/children?\$top=20&\$select=id,name,size,lastModifiedDateTime,folder,file" \
  | jq '.value[] | {id, name, size, kind: (if .folder then "folder" else .file.mimeType end), modified: .lastModifiedDateTime}'
```

Folders have `"folder":{"childCount":N}`, files have `"file":{"mimeType":"..."}`.

### List files in a sub-folder by path

```sh
curl -sS -H "Authorization: Bearer $MICROSOFT_ONEDRIVE_TOKEN" \
  "https://graph.microsoft.com/v1.0/me/drive/root:/Documents:/children?\$top=20&\$select=id,name,size,lastModifiedDateTime"
```

Path uses `:` as the path/segment separator — `:/Documents/Q1:/children`.

### Search files (recursive)

```sh
curl -sS -H "Authorization: Bearer $MICROSOFT_ONEDRIVE_TOKEN" \
  --data-urlencode "q=quarterly report" --get \
  "https://graph.microsoft.com/v1.0/me/drive/root/search(q='quarterly report')?\$top=25&\$select=id,name,size,webUrl,lastModifiedDateTime"
```

> `search(q='')` with empty query returns 400. To find files by type
> without a keyword, search by extension: `search(q='.pdf')`.

### Recently modified files (cross-folder)

```sh
curl -sS -H "Authorization: Bearer $MICROSOFT_ONEDRIVE_TOKEN" \
  "https://graph.microsoft.com/v1.0/me/drive/recent?\$top=25" \
  | jq '.value[] | {name, modified: .lastModifiedDateTime, parent: .parentReference.path}'
```

### Files shared with me

```sh
curl -sS -H "Authorization: Bearer $MICROSOFT_ONEDRIVE_TOKEN" \
  "https://graph.microsoft.com/v1.0/me/drive/sharedWithMe?\$top=25" \
  | jq '.value[] | {name, size: .size, owner: .remoteItem.shared.owner.user.displayName}'
```

### Download a file by item id

```sh
# /content returns 302 to a pre-signed URL — let curl follow it.
curl -sSL -H "Authorization: Bearer $MICROSOFT_ONEDRIVE_TOKEN" \
  "https://graph.microsoft.com/v1.0/me/drive/items/${ITEM_ID}/content" \
  -o "$SKILL_DIR/tmp/$(basename "$NAME")"
```

### Download a file by path

```sh
# URL-encode each path segment with jq -Rr @uri (or use printf encoding).
ENCODED=$(printf '%s' "Documents/report.docx" | jq -sRr @uri)
curl -sSL -H "Authorization: Bearer $MICROSOFT_ONEDRIVE_TOKEN" \
  "https://graph.microsoft.com/v1.0/me/drive/root:/${ENCODED}:/content" \
  -o report.docx
```

### Upload a small file (< 4 MB)

```sh
curl -sS -X PUT \
  -H "Authorization: Bearer $MICROSOFT_ONEDRIVE_TOKEN" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @/tmp/report.pdf \
  "https://graph.microsoft.com/v1.0/me/drive/root:/Documents/report.pdf:/content"
```

For files **> 4 MB** use an upload session (chunked):

```sh
# 1) create session
SESSION=$(curl -sS -X POST \
  -H "Authorization: Bearer $MICROSOFT_ONEDRIVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"item":{"@microsoft.graph.conflictBehavior":"rename"}}' \
  "https://graph.microsoft.com/v1.0/me/drive/root:/Documents/big.zip:/createUploadSession")
UPLOAD_URL=$(echo "$SESSION" | jq -r .uploadUrl)
# 2) PUT in 10 MiB chunks with Content-Range: bytes <start>-<end>/<total>
# (See Microsoft Graph docs for the chunking loop; jq + dd makes this trivial.)
```

### Create a folder

```sh
curl -sS -X POST \
  -H "Authorization: Bearer $MICROSOFT_ONEDRIVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Reports","folder":{},"@microsoft.graph.conflictBehavior":"rename"}' \
  https://graph.microsoft.com/v1.0/me/drive/root/children
```

`@microsoft.graph.conflictBehavior`: `rename` (auto-suffix), `replace`
(overwrite), `fail` (error if exists). Default is `fail`.

### Rename / move (PATCH)

**⚠️ Always show the source and destination before executing.**

```sh
# Rename only
curl -sS -X PATCH \
  -H "Authorization: Bearer $MICROSOFT_ONEDRIVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"renamed.docx"}' \
  "https://graph.microsoft.com/v1.0/me/drive/items/${ITEM_ID}"

# Move to a different folder
curl -sS -X PATCH \
  -H "Authorization: Bearer $MICROSOFT_ONEDRIVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(jq -nc --arg pid "$NEW_PARENT_ID" '{parentReference:{id:$pid}}')" \
  "https://graph.microsoft.com/v1.0/me/drive/items/${ITEM_ID}"
```

### Delete

**⚠️ Always fetch the item name first and confirm with the user.**

```sh
# 1) Show what will be deleted
curl -sS -H "Authorization: Bearer $MICROSOFT_ONEDRIVE_TOKEN" \
  "https://graph.microsoft.com/v1.0/me/drive/items/${ITEM_ID}?\$select=name,size,lastModifiedDateTime" \
  | jq '"Delete \(.name) (\(.size) bytes, modified \(.lastModifiedDateTime))?"'

# 2) After user confirms (returns 204 No Content)
curl -sS -X DELETE -H "Authorization: Bearer $MICROSOFT_ONEDRIVE_TOKEN" \
  "https://graph.microsoft.com/v1.0/me/drive/items/${ITEM_ID}" \
  -w "HTTP %{http_code}\n"
```

### Create a sharing link

**⚠️ Confirm with the user before sharing — this exposes data externally.**

```sh
curl -sS -X POST \
  -H "Authorization: Bearer $MICROSOFT_ONEDRIVE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"view","scope":"organization"}' \
  "https://graph.microsoft.com/v1.0/me/drive/items/${ITEM_ID}/createLink" \
  | jq '.link.webUrl'
```

`type`: `view` | `edit` | `embed`. `scope`: `anonymous` | `organization` | `users`.

### List SharePoint sites

Requires `Sites.Read.All`.

```sh
curl -sS -H "Authorization: Bearer $MICROSOFT_ONEDRIVE_TOKEN" \
  "https://graph.microsoft.com/v1.0/sites?search=*&\$top=10" \
  | jq '.value[] | {id, name: .displayName, webUrl}'
```

Files inside a site:

```sh
curl -sS -H "Authorization: Bearer $MICROSOFT_ONEDRIVE_TOKEN" \
  "https://graph.microsoft.com/v1.0/sites/${SITE_ID}/drive/root/children?\$top=20"
```

## OData quick reference

| Param | Example |
|---|---|
| `$select` | `id,name,size,lastModifiedDateTime` |
| `$filter` | `name eq 'report.docx'`, `size gt 1000000` |
| `$orderby` | `lastModifiedDateTime desc` |
| `$top` | `10` browsing, `25` search |
| `$expand` | `children`, `permissions` |

Use `--data-urlencode "$key=$value" --get` with curl to avoid shell-quoting `$` and spaces.

## Rules

- **Always pass `$select`** — defaults return 30+ fields per item.
- **`$top=10`** for browse, `25` for search. Don't paginate past 50 unless asked.
- **URL-encode IDs** if using them in a path — IDs can contain `+`, `/`, `=`. Use `jq -sRr @uri`.
- **Empty `search(q='')` returns 400** — search by extension if you don't have a keyword.

## CRITICAL: User consent for destructive actions

**Never** delete, overwrite or share without explicit confirmation. Pattern: **prepare → present → execute**.

| Action | What to show user |
|---|---|
| Delete | "Delete '{name}' ({size} bytes, modified {date})?" |
| Overwrite (`@microsoft.graph.conflictBehavior=replace`) | "Overwrite '{name}'? Existing: {size}, modified {date}" |
| Share (`createLink`) | "Create {type} link for '{name}' with {scope} access?" |
| Move | "Move '{name}' from {old folder} to {new folder}?" |
| Bulk | Count + sample: "Delete 12 files in /Reports/?" |

## Errors

- `401 InvalidAuthenticationToken` → token expired; user must reinstall the connector.
- `403 accessDenied` → scope missing (e.g. trying to write with read-only token); ask user to reinstall and tick the write scope.
- `429 TooManyRequests` → respect the `Retry-After` header (in seconds).
- `404 itemNotFound` → wrong id or path; double-check casing.

## Reference

For deep dives consult Microsoft's docs:
- Drive items: <https://learn.microsoft.com/en-us/graph/api/resources/driveitem>
- Upload large files: <https://learn.microsoft.com/en-us/graph/api/driveitem-createuploadsession>
- Sharing: <https://learn.microsoft.com/en-us/graph/api/driveitem-createlink>
