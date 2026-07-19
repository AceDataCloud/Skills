# Publish image, video, or long-article notes

## Collect and validate

Build one JSON preview and run `validate-publish` before opening creator controls:

- `type`: `image`, `video`, or `long_article`.
- `title`, `content`, `tags`, `visibility`, optional `schedule_at`, `products`, and image-only `is_original`.
- `media`: Ace Data Cloud CDN URLs for automatic upload. Image requires at least one; video requires exactly one.
- `now`: current timezone-aware ISO 8601 time when validating a schedule.

The helper preflights only the constraints available without network access: HTTPS Ace Data Cloud CDN origin and at most 20 URLs. During `browser.file_upload`, the extension independently enforces image/video content type, at most 32 MiB per file, 64 MiB total, declared `Content-Length`, no redirect, and a 30-second download timeout. A helper success does not prove that media passed those runtime checks. Local, private, third-party, redirecting, or larger media must be selected by the user in the page. Never request filesystem paths.

The helper validates the conservative known contract. The visible creator UI remains authoritative: if it shows a stricter title, schedule, media, or account limit, obey the UI and regenerate the preview.

## Preview and confirmation

Show the exact normalized preview: post type, title, full body, tags, media names/count, long-article template, products, visibility, originality, and schedule. Wait for explicit confirmation. If any value changes, validate and confirm again.

## Execute

1. Ask the user to open `https://creator.xiaohongshu.com`, attach that tab, and locally verify the signed-in account.
2. Read the page and stop on warnings or unexpected account context.
3. Select image, video, or long-article mode using fresh refs.
4. Upload approved CDN media through `browser.file_upload`, or wait for the user to select local media. Read until exact filenames/thumbnails and processing completion are visible.
5. Fill title/body using fresh refs. For rich-text editors, read immediately after input; if the exact value is not visible, stop rather than repeatedly injecting it.
6. Add tags/topics, template/layout, products, visibility, originality, and schedule one at a time. Read and verify each state.
7. Before the final action, read again and compare every visible field with the confirmed preview. Stop on mismatch.
8. Click Publish/Schedule exactly once after the final local approval.
9. Follow [reconciliation](./reconciliation.md). Report success only from a visible success state or destination, and include the canonical URL when available.

Never mix image/video media unless the visible current UI explicitly supports it. Bind products only when the account visibly exposes the feature and the exact selected products appear in the final preview.