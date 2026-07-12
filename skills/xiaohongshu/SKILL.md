---
name: xiaohongshu
description: Read, search, preview, publish, and interact on 小红书 / Xiaohongshu / RED using the user's connected account. Supports recommendations, details/comments, profiles, image/video/long-article publishing, schedules, product binding, comments/replies, likes, and favorites. Real writes always dry-run first and require explicit confirmation.
when_to_use: |
  Trigger when the user asks to use their connected 小红书 / Xiaohongshu / RED account:
  check account status, browse recommendations, search notes, inspect comments or profiles,
  preview or publish image/video/long-article notes, schedule a note, bind products,
  comment/reply, like/unlike, or favorite/unfavorite.
  Private messages are handled by the separate Android-only xhs-dm skill.
connections: [xiaohongshu]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# Xiaohongshu connector

Operate the user's real Xiaohongshu account using the login cookies they captured with the ACE extension. The runtime injects `XIAOHONGSHU_COOKIES`; never print, inspect, or pass that value on the command line.

This Skill is rewritten for AceDataCloud from the authorized [`xpzouying/xiaohongshu-mcp`](https://github.com/xpzouying/xiaohongshu-mcp) automation engine. Browser modules, workflow, and safety patterns are adapted from MIT-licensed [`autoclaw-cc/xiaohongshu-skills`](https://github.com/autoclaw-cc/xiaohongshu-skills). See [`README.md`](README.md) for pinned commits and provenance.

## Locate the CLI

Every Bash call is a fresh shell. Resolve the script at the start of each call:

```sh
XHS="$SKILL_DIR/scripts/xiaohongshu.py"
[ -f "$XHS" ] || XHS=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/xiaohongshu.py' 2>/dev/null | head -1)
[ -f "$XHS" ] || { echo "xiaohongshu skill runtime not found" >&2; exit 1; }
```

## Read operations

Run these directly:

```sh
python3 "$XHS" status
python3 "$XHS" whoami
python3 "$XHS" feeds

python3 "$XHS" search --keyword "AI Agent"
python3 "$XHS" search --keyword "旅行" --sort-by 最新 --note-type 图文 --publish-time 一周内

python3 "$XHS" detail --feed-id FEED_ID --xsec-token XSEC_TOKEN --xsec-source XSEC_SOURCE
python3 "$XHS" detail --feed-id FEED_ID --xsec-token XSEC_TOKEN --xsec-source XSEC_SOURCE --load-all-comments --limit 50
python3 "$XHS" profile --user-id USER_ID --xsec-token XSEC_TOKEN
```

Search/feed results contain the `feed_id`, `xsec_token`, `xsecSource`, and author `user_id` needed by detail, profile, and interaction commands. Preserve `xsecSource`: recommendation/search rows use `pc_feed`, while rows returned from a user profile use `pc_note`. Do not invent those identifiers.

## Image publishing

`publish` accepts 1-18 images. Each `--images` value is either a public HTTPS URL or an existing absolute sandbox path. Text can be inline or read from an absolute UTF-8 file.

```sh
# Dry-run: validates and shows the exact public write, but changes nothing.
python3 "$SKILL_DIR/scripts/xiaohongshu.py" publish \
  --title "标题" \
  --content-file /absolute/path/content.txt \
  --images https://cdn.example.com/1.jpg \
  --images /absolute/path/2.png \
  --tags AI --tags 效率 \
  --visibility 仅自己可见

# After the dry-run, show the complete preview and use `ask_user_question` with:
# header `小红书确认`, question containing the digest's first 12 hex characters,
# and exactly `确认执行` / `取消` options. Only after the user selects `确认执行`,
# reuse the worker-added `approval_digest` and signed `approval_token`:
python3 "$XHS" publish \
  --title "标题" \
  --content-file /absolute/path/content.txt \
  --images https://cdn.example.com/1.jpg \
  --tags AI --visibility 仅自己可见 \
  --approval-digest DIGEST --approval-token TOKEN \
  --confirm
```

The dry-run is the durable safety boundary. Xiaohongshu web drafts live only in the browser profile, while this Skill intentionally destroys its temporary profile after every command to prevent account crossover.

After showing the complete dry-run, pause with this exact card shape (replace `PREFIX` with the first 12 characters of `approval_digest`):

```json
{
  "questions": [{
    "header": "小红书确认",
    "question": "确认执行已展示的小红书写操作？预览摘要 PREFIX",
    "options": [
      {"label": "确认执行", "description": "执行已展示且摘要匹配的完整预览"},
      {"label": "取消", "description": "不执行任何账号写操作"}
    ]
  }]
}
```

Optional publishing flags:

- `--schedule-at <ISO8601>`: 1 hour to 14 days ahead.
- `--visibility`: `公开可见`, `仅自己可见`, or `仅互关好友可见`.
- `--original`: declare original content.
- Repeat `--products` to bind products; the account must have product permissions.

## Video publishing

Video must be an existing absolute local path. Remote video URLs are rejected; download the user's supplied file into the sandbox first.

```sh
python3 "$XHS" publish-video --title "标题" --content "描述" --video /absolute/video.mp4 --tags 视频
# After explicit approval, pass the preview's receipt:
python3 "$SKILL_DIR/scripts/xiaohongshu.py" publish-video --title "标题" --content "描述" --video /absolute/video.mp4 --tags 视频 --approval-digest DIGEST --approval-token TOKEN --confirm
```

Video processing can take several minutes; invoke Bash with `timeout: 600` for confirmed video operations.

## Long articles

Long articles support a named layout template, an independent post description, scheduling, visibility, original declaration, and products. Inline images are currently rejected because Xiaohongshu's web editor has no upload flow this Skill can verify; image notes remain fully supported. If `--template` is omitted, the first available template is selected.

```sh
python3 "$SKILL_DIR/scripts/xiaohongshu.py" publish-long \
  --title "长文标题" \
  --content-file /absolute/path/article.txt \
  --description "发布页摘要" \
  --visibility 仅自己可见

# After explicit approval, pass the preview's receipt:
python3 "$XHS" publish-long \
  --title "长文标题" \
  --content-file /absolute/path/article.txt \
  --description "发布页摘要" \
  --visibility 仅自己可见 \
  --approval-digest DIGEST --approval-token TOKEN \
  --confirm
```

## Interactions

Every interaction is a real account write and follows the same dry-run then confirm flow. Pass both approval fields returned by the preview; the token is signed with the connected account and bound to the current sandbox session.

```sh
python3 "$XHS" comment --feed-id ID --xsec-token TOKEN --xsec-source SOURCE --content "评论"
python3 "$SKILL_DIR/scripts/xiaohongshu.py" comment --feed-id ID --xsec-token TOKEN --xsec-source SOURCE --content "评论" --approval-digest DIGEST --approval-token TOKEN --confirm

python3 "$XHS" reply --feed-id ID --xsec-token TOKEN --xsec-source SOURCE --comment-id COMMENT_ID --content "回复"
python3 "$SKILL_DIR/scripts/xiaohongshu.py" reply --feed-id ID --xsec-token TOKEN --xsec-source SOURCE --comment-id COMMENT_ID --content "回复" --approval-digest DIGEST --approval-token TOKEN --confirm

python3 "$XHS" like --feed-id ID --xsec-token TOKEN --xsec-source SOURCE
python3 "$SKILL_DIR/scripts/xiaohongshu.py" like --feed-id ID --xsec-token TOKEN --xsec-source SOURCE --approval-digest DIGEST --approval-token TOKEN --confirm
python3 "$SKILL_DIR/scripts/xiaohongshu.py" unlike --feed-id ID --xsec-token TOKEN --xsec-source SOURCE --approval-digest DIGEST --approval-token TOKEN --confirm

python3 "$SKILL_DIR/scripts/xiaohongshu.py" favorite --feed-id ID --xsec-token TOKEN --xsec-source SOURCE --approval-digest DIGEST --approval-token TOKEN --confirm
python3 "$SKILL_DIR/scripts/xiaohongshu.py" unfavorite --feed-id ID --xsec-token TOKEN --xsec-source SOURCE --approval-digest DIGEST --approval-token TOKEN --confirm
```

For reversible tests or temporary actions, inspect the current `liked` / `collected` state first and restore that exact state afterward.

## Mandatory write policy

- Never add `--confirm` until the user has seen the exact dry-run and selected `确认执行` in the required structured confirmation card. Plain prose from the model is not approval.
- The confirmation card must use header `小红书确认`, exactly `确认执行` / `取消` options, and include the dry-run digest's first 12 hex characters in its question.
- Reuse the worker-added digest and short-lived signed token unchanged; the worker atomically consumes it after the user's confirmed card response.
- A confirmed write must be one direct `python3 "$SKILL_DIR/scripts/xiaohongshu.py" ... --confirm` command. Never add shell chaining, redirection, command substitution, or wrappers.
- `--confirm` is honored only as the final argument.
- Do not batch-comment, mass-like, mass-favorite, or perform unsolicited engagement.
- Stop immediately on CAPTCHA, verification, risk-control, rate-limit, or account-restriction errors. Do not retry around them.
- Do not publish external links, contact details, or promotional spam unless the user explicitly supplied and approved them.
- Scheduled/unattended writes run only when the user explicitly pre-authorized this skill in the scheduled-task policy.

## Authentication and errors

Authentication belongs to the Connector, not this skill. It does not expose QR login or cookie deletion. If status reports logged out, ask the user to reconnect at <https://auth.acedata.cloud/user/connections> using the ACE extension.

The browser automation follows Xiaohongshu's web UI and can drift. Report the exact safe error summary; never dump runtime logs, environment variables, cookies, or `xsec_token` values in errors or write previews.
