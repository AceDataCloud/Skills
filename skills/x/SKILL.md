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
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# x — read & post on X (Twitter) via your own cookies

Drives the user's **real** X account through X's internal web API via
[`tweety-ns`](https://github.com/mahrtayyab/tweety), authenticated by the login
cookie they captured with the ACE extension. No official API key, no cost.

> ⚠️ **Not yet E2E-verified.** Built against tweety-ns's documented API but not
> run against a live account at build time. The first live run is the
> verification — if X's internal API drifted it surfaces as a clear error, not
> silent breakage.

The connector injects the cookie jar as an env var:

- `X_COOKIES` — a JSON array of cookies (needs at least `auth_token` + `ct0`).
  **Secret — full account access. Never echo or print it.**

## Setup — call the shipped CLI

`tweety-ns` is preinstalled in the sandbox. If it's ever missing, bootstrap it
(same pattern as the telegram skill), then call the CLI:

```sh
python3 -c "import tweety" 2>/dev/null || pip install --user --quiet tweety-ns 2>/dev/null || true
X=$SKILL_DIR/scripts/x.py
python3 $X whoami          # who is logged in
```

## Read commands (run directly)

```sh
python3 $X whoami                                            # the logged-in account
python3 $X search --query "ai agents" --product Latest --limit 20   # Top | Latest | Media
python3 $X search-users --query "openai" --limit 10
python3 $X timeline --limit 20                               # my home timeline (latest)
python3 $X user-tweets --user elonmusk --type Tweets --limit 20     # Tweets | Replies | Media
python3 $X tweet --id 1234567890123456789                    # single tweet (id or URL)
python3 $X trends --limit 20                                 # local trending topics
```

`--user` accepts an `@screen_name` (the `@` is optional) or a numeric id.

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
python3 $X post --text "worth reading" --quote https://x.com/u/status/123 --confirm  # quote (id or URL)
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
- **tweety-ns is a scraper of X's non-public API.** It can break when X changes
  its internal endpoints (though it is actively maintained). A "Couldn't get
  … indices" / transaction-id error means tweety needs upgrading:
  `pip install --user -U tweety-ns`. An auth error means the cookie expired →
  reconnect.
- **ToS / rate-limit / ban risk.** This acts through the web API, not the
  official API — high-frequency automation can get the account rate-limited or
  set to read-only / suspended. Keep volume human-like.
- **Never print `X_COOKIES`** — it is full account access. The CLI writes the
  session to an ephemeral temp dir and deletes it; the cookie is never left on disk.
- **DMs are intentionally not exposed** by this skill.
