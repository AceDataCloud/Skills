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

Response:

```json
{"file_url": "https://cdn.acedata.cloud/7f849b80b9.mp4"}
```

→ use `file_url`. One file per request (loop for several).

## When to use

- **Feed a generated asset into another API by URL** — e.g. upload a gpt-image-2 still, then pass its URL to `seedance` / `kling` image-to-video.
- **Publish/return a finished artifact** (final video, cover image).
- **Persist intermediate artifacts** so a later run can re-download and continue.

## Notes

- Auth uses the **platform token** (`ACEDATACLOUD_PLATFORM_TOKEN`), not the per-service API token — the files endpoint is on `platform.acedata.cloud`, not `api.acedata.cloud`.
- If your runtime ships a bundled uploader (e.g. a worker that owns the storage creds), prefer it — it avoids handling the platform token directly.
- The returned URL is CDN-served and stable; safe to store and re-download later.
