---
name: bilibili
description: Read and publish 专栏 articles on Bilibili (bilibili.com) with the user's own login cookies (BYOC) — list their published articles with view/like/comment stats, inspect one article, and publish a new article. Use when the user mentions Bilibili / B站 / 专栏, "我的B站专栏", reading article stats (阅读/点赞), or publishing/投稿 a 专栏 article.
when_to_use: |
  Trigger for anything on the user's Bilibili (bilibili.com) 专栏 account driven
  by their own login cookie: show who they are, list their published 专栏
  articles with view / like / comment counts, look at one article's stats, or
  publish a new 专栏 article. This acts as the user's real account, so writes are
  gated behind an explicit confirmation.
connections: [bilibili]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# bilibili — read & publish 专栏 via your own cookies

Drives the user's **real** Bilibili 专栏 (article) account through the same
`api.bilibili.com` web endpoints the site uses, authenticated by the login
cookie they captured with the ACE extension. No browser, no third-party deps —
`urllib` + `hashlib` (the article-list read endpoint needs WBI signing, done
with stdlib).

The connector injects the cookie jar as an env var:

- `BILIBILI_COOKIES` — a JSON array of cookies. **Secret — never echo or print
  it.** It includes `SESSDATA` (auth) and `bili_jct` (the CSRF token used for
  writes).

## CLI

The skill ships [`scripts/bilibili.py`](scripts/bilibili.py) — self-contained, stdlib only.

```sh
BILI=$SKILL_DIR/scripts/bilibili.py
python3 $BILI whoami                       # who is logged in (mid, name)
python3 $BILI articles --limit 20          # my 专栏 articles + stats
python3 $BILI article <cvid>               # one article's stats (cv id)
```

Stats come straight from Bilibili: `view` (阅读), `like` (点赞), `reply` (评论),
`favorite` (收藏), `coin` (投币).

## Verify the connection first

```sh
python3 $BILI whoami
# → {"mid": 91207595, "name": "...", "level": 4}
```

On a not-logged-in / auth error the cookie is expired — have the user reconnect
at <https://auth.acedata.cloud/user/connections>. Do **not** loop-retry.

## Publishing — GATED (dry-run unless trailing `--confirm`)

`publish` writes to the user's real account. 专栏 content is **HTML**. Without a
trailing `--confirm` it dry-runs. `--confirm` is honored **only as the last
argument**. Always show the dry-run, get an explicit "yes", then re-run.

```sh
python3 $BILI publish --title "标题" --content-file a.html                       # dry-run
python3 $BILI publish --title "标题" --content-file a.html --draft-only --confirm   # save a draft
python3 $BILI publish --title "标题" --content-file a.html --confirm                # save draft + submit (publish)
```

- `--draft-only` saves a draft (no submit) — safe; finish/publish in the editor.
- The **submit** (go public) step is frequently rate-limited by Bilibili
  risk-control (HTTP 412). When that happens the CLI reports the saved draft +
  edit URL so the user can publish from the web editor. Default to `--draft-only`.

## Gotchas

- **This is the user's real Bilibili account.** Confirm before any publish.
- **submit may 412** (anti-bot) even when the draft saved fine — the draft is the
  reliable result; don't loop-retry submit.
- A wrong cover layout (`tid`) / category returns `-17`; the CLI auto-retries
  common `tid` values.
- **Never print `BILIBILI_COOKIES`** — it is full account access.
- **ToS**: acts only on the user's own account with their own captured cookie.
