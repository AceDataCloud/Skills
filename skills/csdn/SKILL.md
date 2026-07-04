---
name: csdn
description: Read and publish on CSDN (blog.csdn.net) with the user's own login cookies (BYOC) — list their published articles with view/like/comment stats, inspect one article, and publish a new article. Use when the user mentions CSDN, "我的 CSDN 文章", reading their article stats (阅读/点赞), or publishing/发文 to CSDN.
when_to_use: |
  Trigger for anything on the user's CSDN (blog.csdn.net) account driven by
  their own login cookie: show who they are, list their published articles with
  view / like / comment counts, look at one article's stats, or publish a new
  article. This acts as the user's real account, so writes are gated behind an
  explicit confirmation.
connections: [csdn]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# csdn — read & publish on CSDN via your own cookies

Drives the user's **real** CSDN account through the same web APIs the site's own
editor uses, authenticated by the login cookie they captured with the ACE
extension. No browser, no third-party deps — `urllib` + `hmac` (the editor's
save endpoint requires an HMAC signature, computed with stdlib).

The connector injects the cookie jar as an env var:

- `CSDN_COOKIES` — a JSON array of cookies. **Secret — never echo or print it.**
  The CLI reads it for you.

> CSDN fronts its APIs with a WAF; the CLI already sends a full browser
> fingerprint so reads aren't 403'd. If you still get a WAF 403, the cookie
> expired — have the user reconnect.

## CLI

The skill ships [`scripts/csdn.py`](scripts/csdn.py) — self-contained, stdlib only.

```sh
CSDN=$SKILL_DIR/scripts/csdn.py
python3 $CSDN whoami                       # who is logged in (+ total article count)
python3 $CSDN articles --limit 20          # my published articles + stats
python3 $CSDN article <article-id>         # one article's stats
```

Stats come straight from CSDN: `view_count` (阅读), `digg_count` (点赞),
`comment_count` (评论), `collect_count` (收藏).

## Verify the connection first

```sh
python3 $CSDN whoami
# → {"username": "...", "nickname": "...", "articles_total": 1597}
```

On a WAF 403 / auth error the cookie is expired — tell the user to reconnect at
<https://auth.acedata.cloud/user/connections>. Do **not** retry in a loop.

## Publishing — GATED (dry-run unless trailing `--confirm`)

`publish` writes to the user's real account. Content is **Markdown**. Without a
trailing `--confirm` it dry-runs. `--confirm` is honored **only as the last
argument**. Always show the dry-run, get an explicit "yes", then re-run with
`--confirm` last.

```sh
python3 $CSDN publish --title "标题" --content-file a.md                      # dry-run
python3 $CSDN publish --title "标题" --content-file a.md --draft-only --confirm  # private draft (status=2)
python3 $CSDN publish --title "标题" --content-file a.md --tags "AI,Python" --confirm  # PUBLIC, goes live
```

- `--draft-only` saves a private draft (CSDN `status=2`) — safe, nothing public.
- Without `--draft-only` the article is **published publicly** under the user's
  name. Default to `--draft-only` unless the user clearly asked to go live.
- `--tags` is a comma-separated list of article tags.

## Images

`publish` automatically re-hosts external markdown images (`![](url)`) onto
CSDN's own CDN (`i-blog.csdnimg.cn`) before saving — CSDN 防盗链 blocks external
images, and saving an article full of external URLs can even time out. Images
already on `csdnimg.cn` are left alone; pass `--no-rehost-images` to skip. An
image that fails to upload keeps its original URL (never blocks the post).

## Gotchas — surface before the user is surprised

- **This is the user's real CSDN account.** Confirm before any publish.
- **Cookie expiry / WAF 403**: reconnect at auth.acedata.cloud/user/connections —
  never loop-retry a WAF block.
- The editor save endpoint is signed with an HMAC key baked into CSDN's web
  bundle; if CSDN rotates it, publish fails loudly (reads still work).
- **Never print `CSDN_COOKIES`** — it is full account access.
- **ToS**: cookie automation acts only on the user's own account with their own
  captured cookie; the user owns that risk.


## Record the output

After you successfully publish and obtain the live result URL, call the built-in
`publish_artifact` tool ONCE so the user can track this deliverable in **My Outputs**:

```
publish_artifact(kind="article", channel="csdn", title="<title>", url="<the REAL returned URL>", status="delivered")
```

Use the real returned URL — never fabricate one. Call it once per published item,
only after delivery is confirmed; skip it (or use `status="failed"`) if publishing failed.
See `_shared/artifacts.md`.
