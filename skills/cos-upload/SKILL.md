---
name: cos-upload
description: Upload a local file to AceData Cloud CDN and get back a public URL. Use whenever you produce a local artifact (image, audio, video, doc) that another API needs as a URL, or that you need to return/persist (e.g. feed a generated image into an image-to-video API, or publish a finished video).
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_PLATFORM_TOKEN (see _shared/authentication.md). Some runtimes instead provide a bundled uploader — prefer that when present.
---

# Upload a file → AceData CDN URL

Turn a local file into a public `https://cdn.acedata.cloud/...` URL.

## Upload (multipart, synchronous)

```bash
curl -s -X POST https://platform.acedata.cloud/api/v1/files/ \
  -H "Authorization: Bearer $ACEDATACLOUD_PLATFORM_TOKEN" \
  -F "file=@/path/to/video.mp4"
```

On HTTP 200, use the returned `file_url` rather than constructing a URL. The platform generates a unique `uploads/<uuid>` path and preserves the uploaded filename's safe extension. The returned `mime` is the MIME type written to object-storage metadata. One file per request (loop for several); the default limit is 100 MB per file.

Use a filename whose extension matches the actual content. The upload part's MIME type is stored as supplied; if omitted or `application/octet-stream`, the platform infers it from the filename using standard MIME mappings. Neither extension handling nor MIME inference converts the file's bytes.

## When to use

- **Feed a generated asset into another API by URL** — e.g. upload a gpt-image-2 still, then pass its URL to `seedance` / `kling` image-to-video.
- **Publish/return a finished artifact** (final video, cover image).
- **Persist intermediate artifacts** so a later run can re-download and continue.

## Notes

- Auth uses the **platform token** (`ACEDATACLOUD_PLATFORM_TOKEN`), not the per-service API token — the files endpoint is on `platform.acedata.cloud`, not `api.acedata.cloud`.
- If your runtime ships a bundled uploader (e.g. a worker that owns the storage creds), prefer it — it avoids handling the platform token directly.
- The returned URL is publicly accessible without authentication; do not upload sensitive data. Retention follows the platform's current storage policy, not a permanent-archive guarantee; use your own object storage for long-term archiving.
