---
name: medium
description: Read and publish on Medium (medium.com) with the user's own login cookies (BYOC) — list their posts with clap/response stats, inspect one post, and publish a new story. Use when the user mentions Medium, "my Medium posts", reading their post stats (claps/reads), or publishing a story to Medium.
when_to_use: |
  Trigger for anything on the user's Medium (medium.com) account driven by their
  own login cookie: show who they are, list their posts with clap / response /
  reading-time data, look at one post, or publish a new story. This acts as the
  user's real account, so writes are gated behind an explicit confirmation.
connections: [medium]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# medium — read & publish on Medium via your own cookies

Drives the user's **real** Medium account through the same internal web API the
site uses (Medium retired its public write API in 2023), authenticated by the
login cookie they captured with the ACE extension. No browser, no third-party
deps — just `urllib`.

The connector injects the cookie jar as an env var:

- `MEDIUM_COOKIES` — a JSON array of cookies (`sid`, `uid`, `xsrf`). **Secret —
  never echo or print it.** The CLI echoes the `xsrf` cookie as the
  `x-xsrf-token` header on writes for you.

## CLI

The skill ships [`scripts/medium.py`](scripts/medium.py) — self-contained, stdlib only.

```sh
MED=$SKILL_DIR/scripts/medium.py
python3 $MED whoami                       # who is logged in
python3 $MED articles --limit 20          # my posts + clap/response stats
python3 $MED article <post-id>            # one post's details
```

## Verify the connection first

```sh
python3 $MED whoami
# → {"user_id": "...", "name": "...", "username": "..."}
```

On an auth error the cookie is expired — have the user reconnect at
<https://auth.acedata.cloud/user/connections>. Do **not** loop-retry.

## Publishing — GATED (dry-run unless trailing `--confirm`)

`publish` writes to the user's real account. Content is **Markdown** (converted
to Medium paragraph blocks: `#`→H1, `##`→H2, `>`→quote, ```` ``` ````→code).
Without a trailing `--confirm` it dry-runs. `--confirm` is honored **only as the
last argument**. Always show the dry-run, get an explicit "yes", then re-run.

```sh
python3 $MED publish --title "Title" --content-file a.md                       # dry-run
python3 $MED publish --title "Title" --content-file a.md --draft-only --confirm   # private draft
python3 $MED publish --title "Title" --content-file a.md --confirm                # PUBLIC story
```

Publishing is Medium's multi-step editor flow (new-story → write deltas →
publish). `--draft-only` stops at the draft (visible only at the user's
`/me/stories/drafts`). Default to `--draft-only` unless the user asked to go live.

## Gotchas

- **This is the user's real Medium account.** Confirm before any publish.
- Markdown→Medium conversion is paragraph-level (headings, quotes, code, body);
  complex inline formatting / images aren't converted — the user can polish in
  the Medium editor before going public.
- Medium sits behind Cloudflare; an occasional 403/429 is transient — the CLI
  auto-retries once after a short pause. A *persistent* 403 means the cookie is
  genuinely expired (reconnect).
- **Never print `MEDIUM_COOKIES`** — it is full account access.
- **ToS**: acts only on the user's own account with their own captured cookie.
