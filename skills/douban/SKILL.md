---
name: douban
description: Use direct HTTP with the user's 豆瓣日记 login cookies to inspect the account and create private notes. Use for 豆瓣日记 article preparation; no paired browser is required for execution.
connections:
  - douban
allowed_tools:
  - Bash
license: Apache-2.0
metadata:
  author: acedatacloud
  version: '2.0'
---

# 豆瓣日记 over HTTP

The connector injects `DOUBAN_COOKIES` as a JSON cookie array. Never print it or remove quoting from cookie values; the client preserves the browser-captured representation.
Use this bundled Python standard-library client. It talks directly to the platform's web endpoints; no local browser or browser fallback runs during execution. Login cookies are initially captured by the ACE extension and encrypted in the connection vault.

```bash
python3 "$SKILL_DIR/scripts/douban.py" whoami
python3 "$SKILL_DIR/scripts/douban.py" post-private --title "标题" --content-file /tmp/article.txt
python3 "$SKILL_DIR/scripts/douban.py" post-private --title "标题" --content-file /tmp/article.txt --confirm
```

`SKILL_DIR` belongs to the most recently loaded skill. When switching back to this platform after loading another skill, load this skill again and immediately invoke its client through `SKILL_DIR`. Do not search shared cache directories for a script: they can contain older bundles.
Without trailing `--confirm`, writes only build a local preview: no cookies or network are accessed. Use `--confirm` only when the user's request authorizes that exact content, account and action. The script does not infer public-publication permission from a draft request.

## Platform contract

**This creates a real private note, not a draft.** The current topic endpoint replaced the old note autosave API. The only write command is `post-private`, always with `accessible=private`; there is no public-publish command. Obtain authorization for creating a private post. Default `text` input is literal prose; use [native content](references/native-content.md) and `--format native` for Draft.js formatting. Report `status=private_post`, never `draft` or public delivery.

## Content and outcomes

- Preserve the complete article. The client does not re-host images or fetch external media. Use already hosted images and verify them in the editor; do not silently strip an image or change the content to make a request pass.
- The default input format is `text`. Plain text does not render Markdown. Native editor JSON must be prepared explicitly and checked against the source before submission.
- Account lookup must succeed before a write. A timeout, non-JSON/WAF page, missing result ID or business error stops the flow. Never retry a write through another route/browser automatically; inspect the original item first.
- Responses expose only selected account/result fields. Raw errors, CSRF tokens and cookies are never printed. HTTP 403 can mean WAF or account restrictions, not necessarily expiry. Reconnect at <https://studio.acedata.cloud/console/connectors> when login is invalid.
- A successful save response is **not** independent readback. Results include `readback_verified=false`; inspect/reopen the returned item before claiming the complete text persisted. No HTTP public publication is implemented.
- Do not call `publish_artifact` as delivered for a draft or private post.

## Protocol evidence

Request/response contracts inspected in [Wechatsync](https://github.com/wechatsync/Wechatsync/blob/42f61e39e214b8d5377d09d788a716defc4abdc0/packages/core/src/adapters/platforms/douban.ts). The Python implementation is independent; no GPL source is bundled. Offline tests verify the wire contract and failure handling, not current live-account publishing access.
