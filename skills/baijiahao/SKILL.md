---
name: baijiahao
description: Read the connected 百家号 / Baijiahao account and save HTML article drafts using the user's own login cookies. Use for 百家号 article preparation and draft creation; public publication is completed in the platform editor.
connections: [baijiahao]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# 百家号 drafts

The connector injects `BAIJIAHAO_COOKIES` as a JSON cookie array. Never print it.
Use the bundled stdlib-only script; resolve this skill's own directory if
`SKILL_DIR` points to another skill loaded in the same turn.

```bash
python3 "$SKILL_DIR/scripts/baijiahao.py" whoami
python3 "$SKILL_DIR/scripts/baijiahao.py" draft \
  --title "标题" --content-file /tmp/article.html
python3 "$SKILL_DIR/scripts/baijiahao.py" draft \
  --title "标题" --content-file /tmp/article.html --confirm
```

The first draft command is a local dry run: no cookies or network are needed.
`--confirm` must be the final argument and actually saves a private draft.
Use it only when the user's request authorizes that draft and its content.
This CLI has no public-publish command; a request to publish should produce
a draft and clearly hand off the returned edit URL for final review/publication.

Prepare an **HTML fragment**, not Markdown source. Render headings, paragraphs,
lists and code blocks before calling the script, and inspect the complete draft
preview. The local size cap is 4 MiB; account/platform limits may be lower.
External images are not downloaded or re-hosted. Verify them in the editor and
upload replacements there if hotlinking fails. The script does not claim
originality, enroll the article in a campaign, or select a public cover.

On expired login, CAPTCHA, WAF or rate-limit errors, inspect the account and
reconnect at <https://auth.acedata.cloud/user/connections> if needed; an HTTP 403
alone does not establish that the cookie expired. Do not retry in a loop.
After any uncertain write, check the existing draft list before another attempt.

Return `draft_id`, `edit_url` and `status=draft`. The editor URL is not a public
article URL. Do not call `publish_artifact` for this draft. Account lookup or a
saved draft does not prove public publication.

## Protocol references

The account endpoint, editor token and draft-save wire format were inspected in
[Wechatsync's Baijiahao adapter](https://github.com/wechatsync/Wechatsync/blob/42f61e39e214b8d5377d09d788a716defc4abdc0/packages/core/src/adapters/platforms/baijiahao.ts)
and cross-checked against the account/editor routes in
[cose](https://github.com/doocs/cose/blob/76c30c0bed8303168dd64288ae27f6094eae27ff/packages/detection/src/configs.js).
The CLI is an independent Python implementation; no GPL source is bundled.
Tests use mocked responses. An authenticated live draft has not been validated
as part of adding this connector.
