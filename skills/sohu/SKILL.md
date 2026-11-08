---
name: sohu
description: Use direct HTTP with the user's 搜狐号 login cookies to inspect the account and save article drafts. Use for 搜狐号 article preparation; no paired browser is required for execution.
connections:
  - sohu
allowed_tools:
  - Bash
license: Apache-2.0
metadata:
  author: acedatacloud
  version: '2.0'
---

# 搜狐号 over HTTP

The connector injects `SOHU_COOKIES` as a JSON cookie array. Never print it.
Use this bundled Python standard-library client. It talks directly to the platform's web endpoints; no local browser or browser fallback runs during execution. Login cookies are initially captured by the ACE extension and encrypted in the connection vault.

```bash
python3 "$SKILL_DIR/scripts/sohu.py" whoami
python3 "$SKILL_DIR/scripts/sohu.py" draft --title "标题" --content-file /tmp/article.html --account-id ACCOUNT_ID
python3 "$SKILL_DIR/scripts/sohu.py" draft --title "标题" --content-file /tmp/article.html --account-id ACCOUNT_ID --confirm
```

Resolve this skill's own directory if `SKILL_DIR` points to another loaded skill.
Without trailing `--confirm`, writes only build a local preview: no cookies or network are accessed. Use `--confirm` only when the user's request authorizes that exact content, account and action. The script does not infer public-publication permission from a draft request.

## Platform contract

Run `whoami` to list accessible subaccounts, then pass an explicit `--account-id`. The script validates that ID against the connected account list and never silently picks the first subaccount. HTML goes to the draft endpoint with `auto=true`; cover/category/originality remain review items in the editor.

## Content and outcomes

- Preserve the complete article. The client does not re-host images or fetch external media. Use already hosted images and verify them in the editor; do not silently strip an image or change the content to make a request pass.
- The default input format is `html`. Plain text does not render Markdown. Native editor JSON must be prepared explicitly and checked against the source before submission.
- Account lookup must succeed before a write. A timeout, non-JSON/WAF page, missing result ID or business error stops the flow. Never retry a write through another route/browser automatically; inspect the original item first.
- Responses expose only selected account/result fields. Raw errors, CSRF tokens and cookies are never printed. HTTP 403 can mean WAF or account restrictions, not necessarily expiry. Reconnect at <https://studio.acedata.cloud/console/connectors> when login is invalid.
- A successful save response is **not** independent readback. Results include `readback_verified=false`; inspect/reopen the returned item before claiming the complete text persisted. No HTTP public publication is implemented.
- Do not call `publish_artifact` as delivered for a draft or private post.

## Protocol evidence

Request/response contracts inspected in [Wechatsync](https://github.com/wechatsync/Wechatsync/blob/42f61e39e214b8d5377d09d788a716defc4abdc0/packages/core/src/adapters/platforms/sohu.ts). The Python implementation is independent; no GPL source is bundled. Offline tests verify the wire contract and failure handling, not current live-account publishing access.
