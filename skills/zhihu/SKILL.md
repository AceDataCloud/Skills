---
name: zhihu
description: Read and publish on Zhihu (知乎) with the user's own login cookies (BYOC) — list published articles & answers with vote/comment stats, inspect an article/answer/question, publish an article, and answer or edit answers to questions. Use when the user mentions 知乎 / Zhihu, "我的知乎文章/回答", reading their stats (点赞/评论), 发文, or 回答/编辑某个问题的回答.
when_to_use: |
  Trigger for anything on the user's Zhihu (知乎) account driven by their own
  login cookie: show who they are, list their published articles or answers
  with vote/comment counts, look at one article / answer / question, publish a
  new article, post a new answer to a question, or edit an existing answer.
  This acts as the user's real account, so writes are gated behind an explicit
  confirmation.
connections: [zhihu]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.2"
---

# zhihu — read & publish on Zhihu via your own cookies

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
python3 $BLOG answers --limit 20           # my published answers + stats
python3 $BLOG answer <answer-id>           # one answer's details + stats
python3 $BLOG question <question-id>       # a question's info + whether I answered it
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
| My latest answers + like/favorite/comment counts | `python3 $BLOG answers --limit 20` |
| Next page (any list) | add `--offset 20` |
| One article's stats | `python3 $BLOG article <id>` |
| One answer's stats (incl. 赞同 voteup) | `python3 $BLOG answer <id>` |
| A question's info + my answer id (if any) | `python3 $BLOG question <id>` |

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
python3 $BLOG publish --title "标题" --content-file article.html               # dry-run
python3 $BLOG publish --title "标题" --content-file article.html --draft-only --confirm  # save a private draft
python3 $BLOG publish --title "标题" --content-file article.html --confirm     # PUBLIC, goes live
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
python3 $BLOG answer-question --question <qid> --content-file ans.html                       # dry-run
python3 $BLOG answer-question --question <qid> --content-file ans.html --draft-only --confirm  # PRIVATE draft (safe)
python3 $BLOG answer-question --question <qid> --content-file ans.html --confirm               # PUBLIC, goes live

# Edit an EXISTING answer (replaces its live, public content)
python3 $BLOG edit-answer --id <answer-id> --content-file ans.html             # dry-run
python3 $BLOG edit-answer --id <answer-id> --content-file ans.html --confirm   # overwrites live answer
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
