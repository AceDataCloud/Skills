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
python3 $BILI drafts --limit 50            # list saved drafts (aid + title)
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

## Managing drafts (the 999-draft cap)

Bilibili caps 专栏 drafts at **999**; once full, saving a new draft fails with
`code 37106 草稿数已达最大上限`. List drafts and delete the ones you don't need:

```sh
python3 $BILI drafts --limit 50                       # list (aid + title)
python3 $BILI delete-draft <aid> <aid2> ...           # dry-run (shows what would delete)
python3 $BILI delete-draft <aid> <aid2> ... --confirm # PERMANENTLY delete those drafts
```

- `delete-draft` is **GATED** (dry-run unless trailing `--confirm`) and deletion
  is **permanent** — always show the dry-run + the titles and get an explicit
  "yes" before `--confirm`. Pass multiple aids to batch a few per call.
- Never bulk-delete blindly: list first, confirm the titles are junk/duplicates.

## Images

`publish` automatically re-hosts external images (both `<img src>` and markdown)
onto Bilibili's CDN (`i0.hdslb.com` / `article.biliimg.com`) before saving —
Bilibili hotlink-blocks external images and rejects the whole article (`37130`)
if any external link remains. webp sources (which upcover rejects) are
transcoded to png via the CDN when possible; an image that still can't upload is
**dropped** from the article rather than failing the post. `--no-rehost-images`
skips this.

## Gotchas

- **This is the user's real Bilibili account.** Confirm before any publish.
- **submit may 412** (anti-bot) even when the draft saved fine — the draft is the
  reliable result; don't loop-retry submit.
- A wrong cover layout (`tid`) / category returns `-17`; the CLI auto-retries
  common `tid` values.
- **Never print `BILIBILI_COOKIES`** — it is full account access.
- **ToS**: acts only on the user's own account with their own captured cookie.
