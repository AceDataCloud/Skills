---
name: weibo
description: Read and post on 微博 / Weibo (weibo.com) with the user's own login cookies (BYOC) — list their recent posts with repost/comment/like counts and publish a new 微博. Use when the user mentions 微博 / Weibo, "我的微博", reading their post engagement, or 发微博 / posting to Weibo.
when_to_use: |
  Trigger for anything on the user's 微博 (weibo.com) account driven by their own
  login cookie: show who they are, list their recent 微博 with repost / comment /
  like counts, or publish a new 微博. This acts as the user's real account, so
  posting is gated behind an explicit confirmation.
connections: [weibo]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# weibo — read & post on 微博 via your own cookies

Drives the user's **real** 微博 account through the same `weibo.com/ajax` web API
the site uses, authenticated by the login cookie they captured with the ACE
extension. No browser, no third-party deps — just `urllib`.

> ⚠️ **Not yet E2E-verified.** Unlike the other cookie skills (csdn / juejin /
> bilibili / medium), this one was built from the documented web API but could
> not be tested against a live account (no 微博 connection existed at build
> time). The first live run is the verification; if an endpoint shape drifted it
> will surface as a clear error rather than silent breakage.

The connector injects the cookie jar as an env var:

- `WEIBO_COOKIES` — a JSON array of cookies. **Secret — never echo or print it.**
  Writes send the `XSRF-TOKEN` cookie as both the `x-xsrf-token` header and the
  `st` form field (the CLI does this for you).

## CLI

The skill ships [`scripts/weibo.py`](scripts/weibo.py) — self-contained, stdlib only.

```sh
# $SKILL_DIR can point at another skill loaded this turn — anchor on our own
# script, and re-run this at the top of every Bash block (fresh shell each time).
WB="$SKILL_DIR/scripts/weibo.py"; [ -f "$WB" ] || WB=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/weibo.py' 2>/dev/null | head -1)
[ -f "$WB" ] || { echo "weibo script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }
python3 "$WB" whoami                     # who is logged in (+ counts)
python3 "$WB" posts --limit 20           # my recent 微博 + engagement
```

Engagement comes straight from 微博: `reposts_count` (转发), `comments_count`
(评论), `attitudes_count` (赞).

## Verify the connection first

```sh
WB="$SKILL_DIR/scripts/weibo.py"; [ -f "$WB" ] || WB=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/weibo.py' 2>/dev/null | head -1)
python3 "$WB" whoami
# → {"uid": "...", "name": "...", "statuses_count": ...}
```

On an auth error the cookie is expired — have the user reconnect at
<https://auth.acedata.cloud/user/connections>. Do **not** loop-retry.

## Posting — GATED (dry-run unless trailing `--confirm`)

微博 are short-form, so there is **no draft step** — a confirmed post goes live.
Without a trailing `--confirm` it dry-runs. `--confirm` is honored **only as the
last argument**. Always show the dry-run, get an explicit "yes", then re-run.

```sh
WB="$SKILL_DIR/scripts/weibo.py"; [ -f "$WB" ] || WB=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/weibo.py' 2>/dev/null | head -1)
python3 "$WB" post --content "你好，这是一条微博"            # dry-run
python3 "$WB" post --content "你好，这是一条微博" --confirm   # PUBLIC 微博 (immediate)
```

- There is **no draft and no private mode** on 微博 — a confirmed post is
  immediately **public**. Always show the dry-run and get explicit approval of
  the exact text before adding `--confirm`.

## Gotchas

- **This is the user's real 微博 account.** Confirm before any post — it is
  immediate and public by default.
- **Not E2E-verified** (see the warning above) — expect to validate the first run.
- **Never print `WEIBO_COOKIES`** — it is full account access.
- **ToS**: acts only on the user's own account with their own captured cookie.
