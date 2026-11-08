---
name: tencentcloud-community
description: Use direct HTTP with the user's 腾讯云开发者社区 login cookies to inspect the account and save article drafts. Use for 腾讯云开发者社区 article preparation; no paired browser is required for execution.
connections:
  - tencentcloudcommunity
allowed_tools:
  - Bash
license: Apache-2.0
metadata:
  author: acedatacloud
  version: '2.0'
---

# 腾讯云开发者社区 over HTTP

The connector injects `TENCENTCLOUDCOMMUNITY_COOKIES` as a JSON cookie array. Never print it.
Use this bundled Python standard-library client. It talks directly to the platform's web endpoints; no local browser or browser fallback runs during execution. Login cookies are initially captured by the ACE extension and encrypted in the connection vault.

```bash
python3 "$SKILL_DIR/scripts/tencentcloud_community.py" whoami
python3 "$SKILL_DIR/scripts/tencentcloud_community.py" draft --title "标题" --content-file /tmp/article.markdown
python3 "$SKILL_DIR/scripts/tencentcloud_community.py" draft --title "标题" --content-file /tmp/article.markdown --confirm
```

Resolve this skill's own directory if `SKILL_DIR` points to another loaded skill.
Without trailing `--confirm`, writes only build a local preview: no cookies or network are accessed. Use `--confirm` only when the user's request authorizes that exact content, account and action. The script does not infer public-publication permission from a draft request.

## Platform contract

The HTTP session must resolve an actual account identity before writing. Markdown is wrapped in the community marker format. The local JSON cap is 900 kB; base64 images are rejected rather than removed. Categories/tags and public submission remain in the editor. This uses community login cookies, not Tencent Cloud SecretId/SecretKey.

## Content and outcomes

- Preserve the complete article. The client does not re-host images or fetch external media. Use already hosted images and verify them in the editor; do not silently strip an image or change the content to make a request pass.
- The default input format is `markdown`. Plain text does not render Markdown. Native editor JSON must be prepared explicitly and checked against the source before submission.
- Account lookup must succeed before a write. A timeout, non-JSON/WAF page, missing result ID or business error stops the flow. Never retry a write through another route/browser automatically; inspect the original item first.
- Responses expose only selected account/result fields. Raw errors, CSRF tokens and cookies are never printed. HTTP 403 can mean WAF or account restrictions, not necessarily expiry. Reconnect at <https://studio.acedata.cloud/console/connectors> when login is invalid.
- A successful save response is **not** independent readback. Results include `readback_verified=false`; inspect/reopen the returned item before claiming the complete text persisted. No HTTP public publication is implemented.
- Do not call `publish_artifact` as delivered for a draft or private post.

## Protocol evidence

Request/response contracts inspected in [MediaSync](https://github.com/yjmm10/MediaSync/blob/77ec95860fd1b0898459a6f401220e34cf80f31e/packages/core/src/adapters/platforms/tencentcloud.ts). The Python implementation is independent; no GPL source is bundled. Offline tests verify the wire contract and failure handling, not current live-account publishing access.
