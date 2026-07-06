---
name: x
description: Read & act on X (Twitter) with the user's own login cookies (BYOC) — post tweets (text / images / video / threads / replies / quotes), search tweets & users, read timelines and single tweets, like / retweet / follow / delete, and see trends. Use when the user mentions X / Twitter, 发推 / 发推特 / 推特, "我的 Twitter", posting to X, searching X, or reading their X timeline.
when_to_use: |
  Trigger for anything on the user's X (Twitter) account driven by their own
  login cookie: post a tweet / thread / reply / quote (optionally with images or
  a video), search tweets or users, read their home timeline or a user's tweets,
  look up one tweet, like / retweet / follow / delete, or check trends. This acts
  as the user's REAL account, so every write is gated behind an explicit
  confirmation.
connections: [x]
allowed_tools: [Bash, publish_artifact]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# x — read & post on X (Twitter) via your own cookies

Drives the user's **real** X account through X's internal web API via
[`twikit`](https://github.com/d60/twikit), authenticated by the login cookie they
captured with the ACE extension. No official API key, no cost.

> ⚠️ **Not yet E2E-verified.** Built against twikit's documented API but not run
> against a live account at build time. The first live run is the verification —
> if X's internal API drifted it surfaces as a clear error, not silent breakage.

The connector injects the cookie jar as an env var:

- `X_COOKIES` — a JSON array of cookies (needs at least `auth_token` + `ct0`).
  **Secret — full account access. Never echo or print it.**

## Setup — verify the shipped CLI

`twikit` is preinstalled in the hosted sandbox image. Do not `pip install` it at
runtime; if import fails, report that the sandbox image is missing the X skill
dependency and stop.

```sh
python3 -c "import twikit" || { echo "sandbox missing twikit; deploy the sandbox skill dependencies image" >&2; exit 1; }
# $SKILL_DIR can point at another skill loaded this turn — anchor on our own
# script (re-run this setup at the top of every fresh-shell Bash block below).
X="$SKILL_DIR/scripts/x.py"; [ -f "$X" ] || X=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/x.py' 2>/dev/null | head -1)
[ -f "$X" ] || { echo "x script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }
python3 "$X" whoami          # who is logged in
```

## Read commands (run directly)

```sh
python3 $X whoami                                            # the logged-in account
python3 $X search --query "ai agents" --product Latest --limit 20   # Top | Latest | Media
python3 $X search-users --query "openai" --limit 10
python3 $X timeline --limit 20                               # my home timeline
python3 $X user-tweets --user elonmusk --type Tweets --limit 20     # Tweets|Replies|Media|Likes
python3 $X tweet --id 1234567890123456789                    # single tweet detail
python3 $X trends --category trending --limit 20             # trending|for-you|news|sports|entertainment
```

`--user` accepts either an `@screen_name` (the `@` is optional) or a numeric id.

## Verify the connection first

```sh
python3 $X whoami
# → {"id": "...", "screen_name": "...", "followers_count": ...}
```

On an auth error the cookie is expired — have the user reconnect at
<https://auth.acedata.cloud/user/connections>. Do **not** loop-retry.

## Write commands — GATED (dry-run unless trailing `--confirm`)

Every state-changing command (`post`, `thread`, `like`, `unlike`, `retweet`,
`unretweet`, `follow`, `unfollow`, `delete`) **dry-runs** without a trailing
`--confirm`. `--confirm` is honored **only as the last argument**, so a tweet
body that merely contains "--confirm" can never silently post. Always show the
dry-run, get an explicit "yes" on the exact text, then re-run with `--confirm`.

```sh
python3 $X post --text "hello world"                          # dry-run
python3 $X post --text "hello world" --confirm                # LIVE tweet
python3 $X post --text "look at this" --media a.jpg,b.png --confirm     # up to 4 images (or 1 video)
python3 $X post --text "great point" --reply-to 123456 --confirm        # reply
python3 $X post --text "worth reading" --quote-url https://x.com/u/status/123 --confirm  # quote
python3 $X thread --text "1/2 first" --text "2/2 second" --confirm       # thread (2+ segments)
python3 $X like --id 123456 --confirm
python3 $X retweet --id 123456 --confirm
python3 $X follow --user elonmusk --confirm
python3 $X delete --id 123456 --confirm                        # delete one of MY tweets
```

- **A confirmed `post` / `thread` is immediately PUBLIC** on the user's real
  account — there is no draft step. Always confirm the exact text first.
- `--media` takes comma-separated file paths. X allows up to **4 images** OR
  **1 video/GIF** per tweet; for a thread the media attaches to the **first**
  segment only.

## Gotchas

- **This is the user's real X account.** Confirm before any write — posts are
  immediate and public.
- **Not E2E-verified** (see the warning above) — expect to validate the first run.
- **twikit is a scraper of X's non-public API.** It can break when X changes its
  internal endpoints. A `Couldn't get KEY_BYTE indices` / transaction-id error
  means twikit's transaction-id bootstrap is currently broken against X; do NOT
  ask the user to reconnect cookies for that error. Report it as upstream drift
  and retry only after the twikit/X compatibility issue is fixed.
- **ToS / rate-limit / ban risk.** This acts through the web API, not the
  official API — high-frequency automation can get the account rate-limited or
  suspended. Keep volume human-like.
- **Never print `X_COOKIES`** — it is full account access.
- **DMs are intentionally not exposed** by this skill.


## Record the output

After you successfully publish and obtain the live result URL, call the built-in
`publish_artifact` tool ONCE so the user can track this deliverable in **My Outputs**:

```
publish_artifact(kind="message", channel="x", title="<title>", url="<the REAL returned URL>", status="delivered")
```

Use the real returned URL — never fabricate one. Call it once per published item,
only after delivery is confirmed; skip it (or use `status="failed"`) if publishing failed.
See `_shared/artifacts.md`.
