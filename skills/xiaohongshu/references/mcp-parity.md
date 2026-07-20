# Xiaohongshu MCP feature parity

This Skill benchmarks its business workflows against `xpzouying/xiaohongshu-mcp` commit
`a7d1f2f7f45e0b1c27de67c8f8a19131ba321725`. Reimplement the behavior through generic
`browser.*` capabilities; never copy its CDP runtime into the extension.

| Reference feature | Skill workflow |
|---|---|
| `check_login_status` | [login status](./login.md#status) |
| `get_login_qrcode` | [QR login](./login.md#qr-login) |
| `publish_content` | [image publish](./publish.md#execute) |
| `publish_with_video` | [video publish](./publish.md#execute) |
| long-article pipeline | [long article steps](./publish.md#execute) |
| `list_feeds` | [recommendations](./browse.md#recommendations) |
| `search_feeds` + five filter groups | [search and filters](./browse.md#search-and-filters) |
| `get_feed_detail` + comment loading | [detail and comments](./browse.md#detail-and-comments) |
| `user_profile` / `get_me` | [profile](./browse.md#profile) |
| `post_comment_to_feed` | [comment](./interactions.md#comment) |
| `reply_comment_in_feed` | [reply](./interactions.md#reply) |
| `like_feed` / unlike | [like and favorite](./interactions.md#like-and-favorite) |
| `favorite_feed` / unfavorite | [like and favorite](./interactions.md#like-and-favorite) |

## Selector recognition hints

These are Xiaohongshu-specific diagnostics owned by this Skill. Use visible semantics first and reacquire
fresh refs after every transition.

- Creator mode tabs: `div.creator-tab`, exact text `上传图文`, `上传视频`, `写长文`.
- Upload input: `input.upload-input`, fallback single visible/associated `input[type=file]`.
- Image completion: `.img-preview-area .pr` count.
- Image/video title: placeholder containing `填写标题`, fallback visible title input.
- Long-title field: `textarea.d-text[placeholder="输入标题"]`.
- Body/editor: `div.tiptap.ProseMirror`, fallback visible `div.ProseMirror[contenteditable=true]`.
- Publish: enabled `xhs-publish-btn`, fallback visible `.publish-page-publish-btn button.bg-red`.
- Comment opener/input/submit: `div.input-box div.content-edit span`, `p.content-input`, `div.bottom button.submit`.
- Like/favorite: `.like-lottie`, `.collect-icon`; always verify resulting state.

Selectors are recognition hints, not permission to run arbitrary JavaScript or CSS queries. If generic
browser observations cannot identify a unique visible target, use a screenshot-bound action or stop.

## Deliberate non-parity

Do not import upstream behaviors that violate the local-browser security boundary:

- no Cookie deletion/export or account state reset;
- no arbitrary CDP/evaluate, remote debugging port, or headless profile;
- no local filesystem paths or direct URL downloads in `browser.file_upload`;
- no hidden `window.__INITIAL_STATE__` extraction; report only visible browser observations;
- no 500-round unattended comment crawling; all loops are bounded and user-request limited.