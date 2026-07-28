# Publish image, video, or long-article notes

## Media is mandatory for image and video notes — settle this before touching the browser

An image note needs at least one image; a video note needs exactly one video; images and video never mix. A `写长文` long article is the one type that carries no uploaded media — its `media` array must stay empty and any illustration is chosen inside the visible editor.

So there is no plain text-only image/video note. If the user asked for one, offer the two real options — supply media (or let you generate an image), or publish it as a long article — **before** opening the creator. Do not navigate, do not open the publish page, and do not report a page problem for what is a product rule.

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

## Working with refs

Every `browser.click` / `browser.fill` / `browser.type` / `browser.upload` needs a `ref` **copied from the output of a `browser.snapshot` or `browser.find` you just ran**. Refs look like `e_<uuid>`. Never pass visible text (`"上传图文"`), a tab ref (`tab_<uuid>`), or a CSS selector as a `ref` — those fail as `stale_target` and no amount of retrying helps.

After every navigation, upload, tab switch, modal open/close, or submission, the old refs are dead: observe again before the next action. When `browser.snapshot` returns a truncated tree on this heavy page, prefer `browser.find` with an exact `role` + `name` for the one control you need.

## Execute

1. Navigate straight to `https://creator.xiaohongshu.com/publish/publish?source=official`. Do not start from `www.xiaohongshu.com` and click through — the publish surface only exists on the `creator.` host, and starting elsewhere costs a cross-host hop for nothing.
2. Wait for load, then allow two seconds for creator widgets and one bounded DOM-settle interval. Read the page and stop on warnings, login redirects, or unexpected account context. A logged-out creator page shows `短信登录` / `发送验证码`: stop and ask the user to log in rather than trying to proceed.
3. The page opens on `上传视频` by default. Select mode by exact visible tab text — `上传图文`, `上传视频`, or `写长文` — by observing the tab strip and clicking the returned ref. Verify the selected mode after clicking; the upload area text changes (`拖拽视频到此或点击上传` for video, an image dropzone for `上传图文`).
4. If the tab click reports success but the mode does not change, an onboarding popover is covering the tab strip. Press `Escape`, re-observe, and click again. If it still does not change, stop and ask the user to dismiss the overlay in the visible tab — never try to delete page nodes.
5. Upload one approved resource at a time and wait until the visible preview count reaches the submitted count before the next resource (up to 60 seconds per image). Re-observe between images: the file input's ref changes after the first upload. For video, wait until processing completes and Publish becomes enabled, up to 10 minutes. If resource resolution is unavailable, wait for the user to select local media and verify the same preview/processing state.
6. Fill the image/video title using the visible title textbox (recognition hints: placeholder containing `填写标题`, then the single visible title input fallback). Titles are capped at 20 full-width-equivalent characters; a visible `n/20` counter turning over the limit is authoritative, so shorten and re-confirm rather than submitting a truncated title. Fill body in the visible rich-text editor (`输入正文描述` placeholder). Use `browser.fill` for replacement, or `browser.click` followed by `browser.type` for rich text. Read immediately after each field; stop if the exact normalized value is not visible.
7. Limit tags to the first 10 confirmed tags. Insert them one at a time, close any topic suggestion popover by focusing the title, and verify visible chips/text before continuing.
8. Configure options one at a time and verify each exact state: schedule (1 hour–14 days), visibility (`公开可见`, `仅自己可见`, `仅互关好友可见`), originality, and products. If originality was requested but cannot be confirmed, abort rather than publishing non-original. Bind a product only when the exact intended product is visibly selected; never accept a first fuzzy match silently.
9. For long article: choose `写长文` → `新的创作`; fill `输入标题` textarea and the body editor; click `一键排版`; enumerate visible template names; select the confirmed template and verify its selected state; click `下一步`; then fill the separate publish-page description editor.
10. Before the final action, read or screenshot again and compare media count, title, full body, tags, options, products, and schedule with the confirmed preview. Stop on mismatch.
11. Locate Publish through two page generations: the visible enabled publish widget first, then the visible legacy red Publish button. Reject `submit-disabled=true`, `disabled`, `aria-disabled=true`, or disabled styling. Click exactly once after the final confirmed chat preview.
12. Follow [reconciliation](./reconciliation.md). Immediate success requires leaving `/publish/publish` or a visible success destination within 15 seconds. Remaining on the form is not success. Return the canonical note URL when visible.

Never mix image/video media unless the visible current UI explicitly supports it. Bind products only when the account visibly exposes the feature and the exact selected products appear in the final preview.

## When a control cannot be reached

If observation returns no usable ref for a control that the visible text clearly shows, do not invent a ref and do not repeat the same failing call. Report which step failed, what the page reads, and hand control to the user. Distinguish these in the report: a **product rule** (text-only note, missing media), a **login/account state** (login form, wrong account), and a **tooling failure** (observation returned no refs) — they need different actions from the user, and calling a tooling failure a page-structure change sends them looking in the wrong place.