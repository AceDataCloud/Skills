---
name: toutiao
description: Read and publish on 今日头条 / Toutiao (mp.toutiao.com) with the user's own login cookies (BYOC) — list their 头条号 articles with impression/read/comment stats, inspect one article, and publish a new 图文 article or draft. Use when the user mentions 今日头条, 头条号, Toutiao, "我的头条文章", reading their article stats (展现/阅读), or 发头条 / publishing to Toutiao.
when_to_use: |
  Trigger for anything on the user's 今日头条号 (mp.toutiao.com) account driven by
  their own login cookie: show who they are, list their articles with impression /
  read / comment counts, look at one article's stats, or publish a new article.
  This acts as the user's real account, so writes are gated behind an explicit
  confirmation.
connections: [toutiao]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# toutiao — read & publish on 今日头条 via your own cookies

Drives the user's **real** 头条号 through the same `mp.toutiao.com` creator APIs
the web console uses, authenticated by the login cookie they captured with the
ACE extension. No browser, no third-party deps — just `urllib`.

The connector injects the cookie jar as an env var:

- `TOUTIAO_COOKIES` — a JSON array of cookies. **Secret — never echo or print
  it.** The CLI reads it for you.

> Writes echo the `csrftoken` cookie back as the `X-CSRFToken` header (the CLI
> does this). Reads and writes are otherwise cookie-only — no request signing.

## CLI

The skill ships [`scripts/toutiao.py`](scripts/toutiao.py) — self-contained, stdlib only.

```sh
# $SKILL_DIR can point at another skill loaded this turn — anchor on our own
# script, and re-run this at the top of every Bash block (fresh shell each time).
TT="$SKILL_DIR/scripts/toutiao.py"; [ -f "$TT" ] || TT=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/toutiao.py' 2>/dev/null | head -1)
[ -f "$TT" ] || { echo "toutiao script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }
python3 "$TT" whoami                       # who is logged in (+ total article count)
python3 "$TT" articles --limit 20          # my articles + stats
python3 "$TT" articles --status draft      # only drafts
python3 "$TT" article <pgc-id>             # one article's stats
```

Stats come straight from 头条: `impression_count` (展现), `read_count` (阅读),
`comment_count` (评论), `digg_count` (点赞).

`--status` accepts `all` (default) / `draft` / `published` / `reviewing` / `failed`.

## Verify the connection first

```sh
TT="$SKILL_DIR/scripts/toutiao.py"; [ -f "$TT" ] || TT=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/toutiao.py' 2>/dev/null | head -1)
python3 "$TT" whoami
# → {"user_id": ..., "name": "...", "articles_total": 0}
```

On an auth error the cookie is expired — tell the user to reconnect at
<https://auth.acedata.cloud/user/connections>. Do **not** retry in a loop.

## Publishing — GATED (dry-run unless trailing `--confirm`)

`publish` writes to the user's real 头条号. Content is **Markdown** (converted to
HTML for 头条's body field). Without a trailing `--confirm` it dry-runs.
`--confirm` is honored **only as the last argument**. Always show the dry-run,
get an explicit "yes", then re-run with `--confirm` last.

```sh
TT="$SKILL_DIR/scripts/toutiao.py"; [ -f "$TT" ] || TT=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/toutiao.py' 2>/dev/null | head -1)
python3 "$TT" publish --title "标题" --content-file a.md                          # dry-run
python3 "$TT" publish --title "标题" --content-file a.md --draft-only --confirm   # private draft
python3 "$TT" publish --title "标题" --content-file a.md --confirm                # PUBLIC, enters 审核
```

- `--draft-only` saves a private draft (`save=1`) — safe, nothing public.
- Without `--draft-only` the article is **submitted publicly** under the user's
  name and enters 头条's 审核 queue. Default to `--draft-only` unless the user
  clearly asked to go live.
- **Titles must be 2–30 characters** — 头条 rejects anything outside that range
  (the CLI fails early with a clear message).

## Images

头条 rejects the **entire article** (`7115 图片uri非法`) if any `<img>` points at
a non-头条 URL — so external images cannot simply be left alone. `publish`
uploads every image in the body to 头条's own CDN first and rewrites the tag with
the CDN attributes 头条 requires.

If an image fails to upload, `publish` **aborts and posts nothing**, listing the
offending URLs — it will not silently publish the user's article with images
missing. Pass `--drop-failed-images` to publish without them instead.
`--no-rehost-images` skips the whole step (头条 will then reject the article
unless the body already carries 头条-hosted images).

## Gotchas — surface before the user is surprised

- **This is the user's real 头条号.** Confirm before any publish.
- **审核**: a published article is not instantly live — 头条 reviews it. The
  returned URL goes live once it passes; a rejected article shows up under
  `articles --status failed`.
- **Daily publish cap**: 头条 caps 图文 posts per day. Hitting it fails the
  publish with 头条's own message — relay it, don't retry in a loop.
- **14-day edit window**: 头条 refuses edits to articles published more than 14
  days ago, so this skill does not offer an edit command.
- **Cookie expiry**: reconnect at auth.acedata.cloud/user/connections.
- **Never print `TOUTIAO_COOKIES`** — it is full account access.
- **ToS**: cookie automation acts only on the user's own account with their own
  captured cookie; the user owns that risk.

## Record the output

After you successfully publish and obtain the live result URL, call the built-in
`publish_artifact` tool ONCE so the user can track this deliverable in **My Outputs**:

```
publish_artifact(kind="article", channel="toutiao", title="<title>", url="<the REAL returned URL>", status="delivered")
```

Use the real returned URL — never fabricate one. Call it once per published item,
only after delivery is confirmed; skip it (or use `status="failed"`) if publishing failed.
See `_shared/artifacts.md`.
