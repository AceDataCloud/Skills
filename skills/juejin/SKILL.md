---
name: juejin
description: Read and publish on 掘金 / Juejin (juejin.cn) with the user's own login cookies (BYOC) — list their published articles with view/like/comment stats, inspect one article, and publish a new article. Use when the user mentions 掘金 / Juejin, "我的掘金文章", reading their article stats (阅读/点赞), or publishing/发文 to 掘金.
when_to_use: |
  Trigger for anything on the user's 掘金 (juejin.cn) account driven by their own
  login cookie: show who they are, list their published articles with view /
  like / comment counts, look at one article, or publish a new article. This
  acts as the user's real account, so writes are gated behind an explicit
  confirmation.
connections: [juejin]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# juejin — read & publish on 掘金 via your own cookies

Drives the user's **real** 掘金 account through the same `api.juejin.cn` web
endpoints the site uses, authenticated by the login cookie they captured with
the ACE extension. No browser, no third-party deps — just `urllib`.

The connector injects the cookie jar as an env var:

- `JUEJIN_COOKIES` — a JSON array of cookies. **Secret — never echo or print it.**

## CLI

The skill ships [`scripts/juejin.py`](scripts/juejin.py) — self-contained, stdlib only.

```sh
# $SKILL_DIR can point at another skill loaded this turn — anchor on our own
# script, and re-run this at the top of every Bash block (fresh shell each time).
JJ="$SKILL_DIR/scripts/juejin.py"; [ -f "$JJ" ] || JJ=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/juejin.py' 2>/dev/null | head -1)
[ -f "$JJ" ] || { echo "juejin script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }
python3 "$JJ" whoami                     # who is logged in (+ totals)
python3 "$JJ" articles --limit 20        # my published articles + stats
python3 "$JJ" article <article-id>       # one article's stats
```

Stats come straight from 掘金: `view_count` (阅读), `digg_count` (点赞),
`comment_count` (评论), `collect_count` (收藏). `audit_status` 2 = online.

## Verify the connection first

```sh
JJ="$SKILL_DIR/scripts/juejin.py"; [ -f "$JJ" ] || JJ=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/juejin.py' 2>/dev/null | head -1)
python3 "$JJ" whoami
# → {"user_id": "...", "name": "...", "post_article_count": 336}
```

On an auth error (`err_no` 401 / "请登录") the cookie is expired — have the user
reconnect at <https://auth.acedata.cloud/user/connections>. Do **not** loop-retry.

## Publishing — GATED (dry-run unless trailing `--confirm`)

`publish` writes to the user's real account. Content is **Markdown**. Without a
trailing `--confirm` it dry-runs. `--confirm` is honored **only as the last
argument**. Always show the dry-run, get an explicit "yes", then re-run.

```sh
JJ="$SKILL_DIR/scripts/juejin.py"; [ -f "$JJ" ] || JJ=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/juejin.py' 2>/dev/null | head -1)
python3 "$JJ" publish --title "标题" --content-file a.md                       # dry-run
python3 "$JJ" publish --title "标题" --content-file a.md --draft-only --confirm   # private draft
python3 "$JJ" publish --title "标题" --content-file a.md \
    --category-id 6809637769959178254 --tag-ids 6809640407484334093 --confirm # PUBLIC
```

- `--draft-only` creates a private draft (掘金 `article_draft`) — safe.
- To **actually publish** (go through 审核), 掘金 requires a valid `--category-id`
  and at least one `--tag-id`. Without them, use `--draft-only` and let the user
  pick category/tags in the 掘金 editor. Default to `--draft-only`.

## Gotchas

- **This is the user's real 掘金 account.** Confirm before any publish.
- Publishing without a category + tag is rejected in 审核; prefer `--draft-only`.
- **Never print `JUEJIN_COOKIES`** — it is full account access.
- **ToS**: acts only on the user's own account with their own captured cookie.


## Record the output

After you successfully publish and obtain the live result URL, call the built-in
`publish_artifact` tool ONCE so the user can track this deliverable in **My Outputs**:

```
publish_artifact(kind="article", channel="juejin", title="<title>", url="<the REAL returned URL>", status="delivered")
```

Use the real returned URL — never fabricate one. Call it once per published item,
only after delivery is confirmed; skip it (or use `status="failed"`) if publishing failed.
See `_shared/artifacts.md`.
