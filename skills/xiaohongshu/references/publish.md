# Publish image, video, or long-article notes

## Collect and validate

Build one JSON preview and run `validate-publish` before opening creator controls:

- `type`: `image`, `video`, or `long_article`.
- `title`, `content`, `tags`, `visibility`, optional `schedule_at`, `products`, and image-only `is_original`.
- `media`: opaque Ace Data Cloud resource IDs for automatic upload. Image requires at least one; video requires exactly one.
- `now`: current timezone-aware ISO 8601 time when validating a schedule.

The helper validates at most 20 bounded opaque resource IDs. Pass them as `resource_ids` to `browser.upload`; never pass URLs or filesystem paths. If the local encrypted resource resolver is unavailable, the upload fails closed and the user must select media in the visible page before handing control back. A helper success never proves that the page accepted or finished processing the media.

The helper validates the conservative known contract. The visible creator UI remains authoritative: if it shows a stricter title, schedule, media, or account limit, obey the UI and regenerate the preview.

## Preview and confirmation

Show the exact normalized preview: post type, title, full body, tags, media names/count, long-article template, products, visibility, originality, and schedule. Wait for explicit confirmation. If any value changes, validate and confirm again.

## Execute

1. Let aichat2 create or reuse the BrowserSession at `https://creator.xiaohongshu.com`, then ask the user to verify the signed-in account when the visible account context is ambiguous.
2. Navigate to `https://creator.xiaohongshu.com/publish/publish?source=official`. Wait for load, then allow two seconds for creator widgets and one bounded DOM-settle interval. Read or screenshot the page and stop on warnings, login redirects, or unexpected account context.
3. Select mode by exact visible tab text: `上传图文`, `上传视频`, or `写长文`. Prefer a fresh semantic ref; if the tab is visually blocked by a popover, stop for user inspection instead of deleting page nodes. Verify the selected mode after clicking.
4. For image posts, upload one approved resource at a time and wait until the visible preview count reaches the submitted count before the next resource (up to 60 seconds per image). For video, wait until processing completes and Publish becomes enabled, up to 10 minutes. If resource resolution is unavailable, wait for the user to select local media and verify the same preview/processing state.
5. Fill the image/video title using the visible title textbox (recognition hints: placeholder containing `填写标题`, then the single visible title input fallback). Fill body in the visible TipTap/ProseMirror contenteditable editor. Use `browser.fill` for replacement, or `browser.click` followed by `browser.type` for rich text. Read immediately after each field; stop if the exact normalized value is not visible.
6. Limit tags to the first 10 confirmed tags. Insert them one at a time, close any topic suggestion popover by focusing the title, and verify visible chips/text before continuing.
7. Configure options one at a time and verify each exact state: schedule (1 hour–14 days), visibility (`公开可见`, `仅自己可见`, `仅互关好友可见`), originality, and products. If originality was requested but cannot be confirmed, abort rather than publishing non-original. Bind a product only when the exact intended product is visibly selected; never accept a first fuzzy match silently.
8. For long article: choose `写长文` → `新的创作`; fill `输入标题` textarea and ProseMirror body; click `一键排版`; enumerate visible template names; select the confirmed template and verify its selected state; click `下一步`; then fill the separate publish-page description editor.
9. Before the final action, read or screenshot again and compare media count, title, full body, tags, options, products, and schedule with the confirmed preview. Stop on mismatch.
10. Locate Publish through two page generations: visible enabled `xhs-publish-btn` widget first, then visible legacy red Publish button. Reject `submit-disabled=true`, `disabled`, `aria-disabled=true`, or disabled styling. Click exactly once after the final confirmed chat preview.
11. Follow [reconciliation](./reconciliation.md). Immediate success requires leaving `/publish/publish` or a visible success destination within 15 seconds. Remaining on the form is not success. Return the canonical note URL when visible.

Never mix image/video media unless the visible current UI explicitly supports it. Bind products only when the account visibly exposes the feature and the exact selected products appear in the final preview.