---
name: zhihu
description: Search Zhihu & the web, get trending topics, and read/publish on Zhihu (知乎) — search Zhihu content or the entire web via the official Developer Platform API, get hot topics (热榜), list published articles & answers with stats, inspect content, publish articles, and answer questions. Use when the user mentions 知乎 / Zhihu, 搜索知乎, 全网搜索, 热榜, "我的知乎文章/回答", reading stats, 发文, or 回答问题.
when_to_use: |
  Trigger for anything involving Zhihu (知乎):
  - Searching Zhihu content (站内搜索) or the entire web (全网搜索)
  - Getting Zhihu trending topics (热榜)
  - Reading the user's own articles/answers with stats
  - Publishing articles or answering questions (gated behind confirmation)
  Search commands use the Zhihu Developer Platform API (Bearer token auth).
  Read/write commands use the user's login cookies (BYOC).
connections: [zhihu]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "2.0"
---

# zhihu — search, read & publish on Zhihu

Two authentication layers, two scripts:

| Script | Auth | Capabilities |
|---|---|---|
| `scripts/search.py` | `ZHIHU_DEVELOPER_TOKEN` (Bearer) | Search Zhihu, search the web, get hot topics |
| `scripts/blog.py` | `ZHIHU_COOKIES` (login cookie) | Read/write own articles & answers |

No browser, no third-party deps — just `urllib`.

The connector injects credentials as env vars:

- `ZHIHU_DEVELOPER_TOKEN` — Zhihu Developer Platform access secret (Bearer token).
  Used for search and hot-list queries. **Secret — never echo or print it.**
- `ZHIHU_COOKIES` — a JSON array of `{name, value, domain, path, ...}` cookies.
  Used for reading/writing the user's own content. **Secret — never echo or print it.**

## Locate the scripts first (every Bash block)

The connector sets `$SKILL_DIR` to this skill's directory, so the scripts live at
`$SKILL_DIR/scripts/`. **Do NOT hard-code `python3 $SKILL_DIR/scripts/…` directly.**
If more than one skill was loaded in the same turn, `$SKILL_DIR` can point at the
*other* skill and the call fails with `No such file or directory` (this is the #1
cause of a Zhihu run silently not finishing). Resolve the path defensively at the
top of **every** Bash block — each Bash call is a fresh shell, so the variable does
not carry over:

```sh
# blog.py is unique to this skill, so it anchors zhihu's dir even if $SKILL_DIR is wrong.
ZDIR="$SKILL_DIR"; [ -f "$ZDIR/scripts/blog.py" ] || ZDIR=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/blog.py' 2>/dev/null | head -1 | sed 's#/scripts/blog.py##')
[ -f "$ZDIR/scripts/blog.py" ] || { echo "zhihu scripts not found (SKILL_DIR=$SKILL_DIR) — is the skill loaded?" >&2; exit 1; }
SEARCH="$ZDIR/scripts/search.py"; BLOG="$ZDIR/scripts/blog.py"
```

Then use `"$SEARCH"` / `"$BLOG"` (always quoted) as shown below.

## Search CLI (search.py)

[`scripts/search.py`](scripts/search.py) — search Zhihu and the web. Requires
only `ZHIHU_DEVELOPER_TOKEN` (no cookies needed).

```sh
# Resolve the scripts first (see "Locate the scripts first" above) — robust to $SKILL_DIR.
ZDIR="$SKILL_DIR"; [ -f "$ZDIR/scripts/blog.py" ] || ZDIR=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/blog.py' 2>/dev/null | head -1 | sed 's#/scripts/blog.py##')
SEARCH="$ZDIR/scripts/search.py"

# Search Zhihu content (站内搜索) — questions, answers, articles
python3 "$SEARCH" search "Python 爬虫"
python3 "$SEARCH" search "Python 爬虫" --count 5

# Search the entire web (全网搜索) — all indexed sites
python3 "$SEARCH" global "AI Agent"
python3 "$SEARCH" global "AI Agent" --count 15

# Filter by site or time
python3 "$SEARCH" global "React" --filter 'host=="github.com"'
python3 "$SEARCH" global "新闻" --filter 'publish_time>=1720000000'
python3 "$SEARCH" global "技术" --filter 'host=="github.com" AND publish_time>=1720000000'
python3 "$SEARCH" global "实时新闻" --db realtime

# Get Zhihu trending topics (热榜)
python3 "$SEARCH" hot
python3 "$SEARCH" hot --limit 10
```

### Search commands

| Goal | Command |
|---|---|
| Search Zhihu (max 10 results) | `python3 "$SEARCH" search "<query>" --count N` |
| Search entire web (max 20) | `python3 "$SEARCH" global "<query>" --count N` |
| Filter by site | `--filter 'host=="example.com"'` |
| Filter by time | `--filter 'publish_time>=<unix_ts>'` |
| Search only realtime/static index | `--db realtime` or `--db static` |
| Zhihu trending topics (max 30) | `python3 "$SEARCH" hot --limit N` |

### Search result fields

**zhihu_search** returns: title, type (Article/Answer), content_id, url,
excerpt, vote_up (赞同), comments, author, authority level, edit_time.

**global_search** returns the same fields plus has_more indicator. The `url`
includes utm tracking params from Zhihu's platform.

**hot_list** returns: rank, title, url, summary, thumbnail.

### global_search Filter syntax

- `host=="example.com"` — filter by domain (note: `host=="zhihu.com"` not
  supported — use `search` command instead)
- `publish_time>=1720000000` — filter by publish time (unix seconds)
- Logical operators: `AND`, `OR` (must be uppercase)
- Parentheses for grouping: `(host=="a.com" OR host=="b.com") AND publish_time>=T`

---

## Blog CLI (blog.py)

The skill ships [`scripts/blog.py`](scripts/blog.py) — self-contained, stdlib only.
Requires `ZHIHU_COOKIES` (login cookie).

```sh
# Resolve the scripts first (see "Locate the scripts first" above) — robust to $SKILL_DIR.
ZDIR="$SKILL_DIR"; [ -f "$ZDIR/scripts/blog.py" ] || ZDIR=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/blog.py' 2>/dev/null | head -1 | sed 's#/scripts/blog.py##')
BLOG="$ZDIR/scripts/blog.py"

# Read (run directly)
python3 "$BLOG" whoami                     # who is logged in
python3 "$BLOG" articles --limit 20        # my published articles + stats
python3 "$BLOG" article <article-id>       # one article's details + stats
python3 "$BLOG" answers --limit 20         # my published answers + stats
python3 "$BLOG" answer <answer-id>         # one answer's details + stats
python3 "$BLOG" question <question-id>     # a question's info + whether I answered it
```

## Verify the connection first

```sh
ZDIR="$SKILL_DIR"; [ -f "$ZDIR/scripts/blog.py" ] || ZDIR=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/blog.py' 2>/dev/null | head -1 | sed 's#/scripts/blog.py##')
python3 "$ZDIR/scripts/blog.py" whoami
# → {"id": "...", "name": "崔庆才丨静觅", "url_token": "Germey", ...}
```

On a `401`/`403` the cookie is expired — tell the user to reconnect at
<https://auth.acedata.cloud/user/connections> (re-capture with the ACE
extension). Do **not** retry in a loop.

## Reading recipes

| Goal | Command |
|---|---|
| Who am I | `python3 "$BLOG" whoami` |
| My latest articles + vote/comment counts | `python3 "$BLOG" articles --limit 20` |
| My latest answers + like/favorite/comment counts | `python3 "$BLOG" answers --limit 20` |
| Next page (any list) | add `--offset 20` |
| One article's stats | `python3 "$BLOG" article <id>` |
| One answer's stats (incl. 赞同 voteup) | `python3 "$BLOG" answer <id>` |
| A question's info + my answer id (if any) | `python3 "$BLOG" question <id>` |

Article stats: `voteup_count` (赞同), `comment_count` (评论). Zhihu does not
expose per-article read counts on these endpoints.

**Answer stat caveat:** the `answers` *list* endpoint does **not** return
`voteup_count` (赞同) — it only exposes `like_count` (喜欢), `favorite_count`
(收藏) and `comment_count`. For the authoritative 赞同 count of an answer, call
`answer <id>` (the single-answer endpoint returns `voteup_count`). `question <id>`
reports `already_answered` + `my_answer_id` so you know whether to use
`answer-question` (new) or `edit-answer` (update).

## Publishing — GATED (dry-run unless trailing `--confirm`)

`publish` writes to the user's real account. Without a trailing `--confirm` it
**dry-runs** (prints what it would do, changes nothing). `--confirm` is honored
**only as the last argument**, so a title/content containing "--confirm" can
never silently go live. Always show the dry-run to the user, get an explicit
"yes", then re-run with `--confirm` last.

```sh
# Content is HTML. For Markdown, convert to HTML first (e.g. `pandoc -f gfm -t html`).
python3 "$BLOG" publish --title "标题" --content-file article.html               # dry-run
python3 "$BLOG" publish --title "标题" --content-file article.html --draft-only --confirm  # save a private draft
python3 "$BLOG" publish --title "标题" --content-file article.html --confirm     # PUBLIC, goes live
```

- `--draft-only` stops after saving a private draft (safe — nothing public).
- Without `--draft-only`, the article is **published publicly** under the user's
  name. Default to `--draft-only` unless the user clearly asked to go live.
- **Images are auto-hosted.** Zhihu strips any `<img>` whose `src` is not on its
  own CDN, so on `--confirm` the CLI re-uploads every external image (HTML
  `<img src>` **and** Markdown `![](url)`, plus `data:` URIs) to Zhihu's image
  service and rewrites the URLs first — images already on `*.zhimg.com` are left
  untouched. The result reports `images: {found, rehosted, failed}`; the dry-run
  reports `images_found`. Pass `--no-images` to skip this. So you can hand the
  CLI HTML/Markdown with normal public image URLs and the pictures survive.

## Answering questions — GATED (dry-run unless trailing `--confirm`)

Two write commands cover the question/answer side. Both gate exactly like
`publish`: no trailing `--confirm` → **dry-run**; `--confirm` is honored **only
as the last argument**. Always show the dry-run, get an explicit "yes", then
re-run with `--confirm` last.

```sh
# Content is HTML (same as articles). For Markdown, convert to HTML first.

# Post a NEW answer to a question
python3 "$BLOG" answer-question --question <qid> --content-file ans.html                       # dry-run
python3 "$BLOG" answer-question --question <qid> --content-file ans.html --draft-only --confirm  # PRIVATE draft (safe)
python3 "$BLOG" answer-question --question <qid> --content-file ans.html --confirm               # PUBLIC, goes live

# Edit an EXISTING answer (replaces its live, public content)
python3 "$BLOG" edit-answer --id <answer-id> --content-file ans.html             # dry-run
python3 "$BLOG" edit-answer --id <answer-id> --content-file ans.html --confirm   # overwrites live answer
```

- **One answer per question.** Zhihu allows a single answer per user per
  question. If the user already answered, `answer-question --confirm` returns a
  clear error telling you to use `edit-answer` instead — find the existing answer
  id with `answers` or `question <qid>` (which reports `my_answer_id`).
- **`--draft-only` is the safe path for new answers** — it saves a *private*
  draft on the question (nothing public). The user reviews it on Zhihu, then you
  re-run without `--draft-only` (with `--confirm`) to publish. Prefer this unless
  the user clearly asked to go live immediately.
- **`edit-answer` has no private mode** — the answer is already public, so any
  `--confirm` edit is live immediately. It preserves the answer's current repost
  setting unless you override with `--repost allowed|disallowed`.
- **转载授权** (`--repost allowed|disallowed`): new answers default to
  `disallowed` (don't grant repost rights); editing keeps the current setting.
- **Images are auto-hosted** for answers too — same behavior and `--no-images`
  flag as `publish`.

## Gotchas — surface before the user is surprised

- **This is the user's real Zhihu account.** Confirm before any publish / answer /
  edit; reading exposes their own private drafts.
- **Cookie expiry**: Zhihu cookies are short-lived. A `401`/`403` means
  reconnect at auth.acedata.cloud/user/connections — never loop-retry.
- **ToS**: cookie automation is against most platforms' terms. This only ever
  acts on the user's own account with their own captured cookie; the user owns
  that risk. Never use it to scrape other people's content at scale.
- **Never print `ZHIHU_COOKIES`** — it is full account access.
- **Scope**: Zhihu only. Other Chinese platforms (掘金 / CSDN / …) ship as their
  own per-platform skills (e.g. `csdn`, `juejin`), each with its own connector —
  not a `--platform` switch here.


## Record the output

After you successfully publish and obtain the live result URL, call the built-in
`publish_artifact` tool ONCE so the user can track this deliverable in **My Outputs**:

```
publish_artifact(kind="article", channel="zhihu", title="<title>", url="<the REAL returned URL>", status="delivered")
```

Use the real returned URL — never fabricate one. Call it once per published item,
only after delivery is confirmed; skip it (or use `status="failed"`) if publishing failed.
See `_shared/artifacts.md`.
