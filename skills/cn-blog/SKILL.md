---
name: cn-blog
description: Read and publish on Chinese content platforms with the user's own login cookies (BYOC) — list their published articles with vote/comment stats, inspect one article, and publish a new article. Use when the user mentions 知乎 / Zhihu, "我的知乎文章", reading their article stats (点赞/评论), or publishing/发文 to Zhihu.
when_to_use: |
  Trigger for anything on the user's Zhihu (知乎) account driven by their own
  login cookie: show who they are, list their published articles with
  vote-up / comment counts, look at one article's stats, or publish a new
  article. This acts as the user's real account, so writes are gated behind
  an explicit confirmation.
connections: [zhihu]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# cn-blog — Zhihu via your own cookies

Drives the user's **real** Zhihu account through the same web APIs the site's
own editor uses, authenticated by the login cookie they captured with the ACE
extension. No browser, no third-party deps — just `urllib`.

The connector injects the cookie jar as an env var:

- `ZHIHU_COOKIES` — a JSON array of `{name, value, domain, path, ...}` cookies.
  **Secret — never echo or print it.** The CLI reads it for you.

## CLI

The skill ships [`scripts/blog.py`](scripts/blog.py) — self-contained, stdlib only.

```sh
BLOG=$SKILL_DIR/scripts/blog.py

# Read (run directly)
python3 $BLOG whoami                       # who is logged in
python3 $BLOG articles --limit 20          # my published articles + stats
python3 $BLOG article <article-id>         # one article's details + stats
```

## Verify the connection first

```sh
python3 $BLOG whoami
# → {"id": "...", "name": "崔庆才丨静觅", "url_token": "cui-qing-cai", ...}
```

On a `401`/`403` the cookie is expired — tell the user to reconnect at
<https://auth.acedata.cloud/user/connections> (re-capture with the ACE
extension). Do **not** retry in a loop.

## Reading recipes

| Goal | Command |
|---|---|
| Who am I | `python3 $BLOG whoami` |
| My latest articles + vote/comment counts | `python3 $BLOG articles --limit 20` |
| Next page | `python3 $BLOG articles --limit 20 --offset 20` |
| One article's stats | `python3 $BLOG article <id>` |

Stats come straight from Zhihu: `voteup_count` (赞同), `comment_count` (评论).
Zhihu does not expose per-article read counts on these endpoints.

## Publishing — GATED (dry-run unless trailing `--confirm`)

`publish` writes to the user's real account. Without a trailing `--confirm` it
**dry-runs** (prints what it would do, changes nothing). `--confirm` is honored
**only as the last argument**, so a title/content containing "--confirm" can
never silently go live. Always show the dry-run to the user, get an explicit
"yes", then re-run with `--confirm` last.

```sh
# Content is HTML. For Markdown, convert to HTML first.
python3 $BLOG publish --title "标题" --content-file article.html               # dry-run
python3 $BLOG publish --title "标题" --content-file article.html --draft-only --confirm  # save a private draft
python3 $BLOG publish --title "标题" --content-file article.html --confirm     # PUBLIC, goes live
```

- `--draft-only` stops after saving a private draft (safe — nothing public).
- Without `--draft-only`, the article is **published publicly** under the user's
  name. Default to `--draft-only` unless the user clearly asked to go live.
- Images: only image URLs already reachable on the public web are kept as-is;
  this CLI does not re-upload local images to Zhihu's CDN.

## Gotchas — surface before the user is surprised

- **This is the user's real Zhihu account.** Confirm before any publish; reading
  exposes their own private drafts.
- **Cookie expiry**: Zhihu cookies are short-lived. A `401`/`403` means
  reconnect at auth.acedata.cloud/user/connections — never loop-retry.
- **ToS**: cookie automation is against most platforms' terms. This only ever
  acts on the user's own account with their own captured cookie; the user owns
  that risk. Never use it to scrape other people's content at scale.
- **Never print `ZHIHU_COOKIES`** — it is full account access.
- **Scope today**: Zhihu only. 掘金 / CSDN connectors exist in the vault and are
  planned next; this skill will grow a `--platform` switch for them.
