---
name: reddit
description: Submit posts (link or text) to subreddits and read your Reddit identity / submissions using either official OAuth or your own Reddit login cookies. Use when the user mentions Reddit, posting to a subreddit, submitting a link or self-post, or checking their Reddit profile / submissions.
when_to_use: |
  Trigger when the user wants to submit a post to a subreddit (link or
  self/text post), or read their own Reddit identity and submissions.
  Posting to a subreddit is public and subject to that subreddit's rules
  / karma requirements — confirm the target subreddit, title and body
  before submitting.
connections: [reddit]
allowed_tools: [Bash, publish_artifact]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "2.0"
  connection_method_preferences:
    reddit/reddit: [oauth, cookie]
---

# Reddit — OAuth or login-cookie access

The connector injects exactly one of these credentials:

- `REDDIT_COOKIES`: JSON cookie array captured by the ACE browser extension.
  It includes `reddit_session` and grants full account access. **Secret — never
  echo, print, log or return it.**
- `REDDIT_TOKEN`: official OAuth bearer token (`identity read submit`).

The helper automatically prefers official OAuth when present and otherwise uses Cookie.
It sends Reddit's required descriptive User-Agent and never forwards cookies
outside `reddit.com`.

## Script resolution

Bash calls do not share shell variables. Resolve the helper inside **every**
fenced Bash invocation before using it:

```sh
R="${SKILL_DIR:-}/scripts/reddit.py"; [ -f "$R" ] || R=$(find /tmp -maxdepth 8 -path '*/skills/*/reddit/scripts/reddit.py' -print -quit 2>/dev/null)
[ -f "$R" ] || { echo "reddit script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }
python3 "$R" whoami
```

If authentication fails, ask the user to reconnect at
<https://auth.acedata.cloud/user/connections>. Do not loop-retry a blocked or
expired session.

## Read

```sh
R="${SKILL_DIR:-}/scripts/reddit.py"; [ -f "$R" ] || R=$(find /tmp -maxdepth 8 -path '*/skills/*/reddit/scripts/reddit.py' -print -quit 2>/dev/null)
[ -f "$R" ] || { echo "reddit script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }
python3 "$R" whoami
python3 "$R" submissions --limit 10
```

## Submit a post — GATED

Posting is public. **Always show the subreddit, final title and final body/URL,
then obtain explicit confirmation.** Without a trailing `--confirm`, both write
commands are dry-runs and make no network request.

```sh
R="${SKILL_DIR:-}/scripts/reddit.py"; [ -f "$R" ] || R=$(find /tmp -maxdepth 8 -path '*/skills/*/reddit/scripts/reddit.py' -print -quit 2>/dev/null)
[ -f "$R" ] || { echo "reddit script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }

# Text post: use a file for long Markdown.
python3 "$R" submit-text --subreddit test --title "My title" --text-file post.md
python3 "$R" submit-text --subreddit test --title "My title" --text-file post.md --confirm

# Link post.
python3 "$R" submit-link --subreddit test --title "My title" --url "https://example.com"
python3 "$R" submit-link --subreddit test --title "My title" --url "https://example.com" --confirm
```

`--confirm` is honored only when it is the final argument. A title or body that
contains the text `--confirm` can never trigger a write.

## Safety and failure handling

- Never print `REDDIT_COOKIES`, `REDDIT_TOKEN`, `reddit_session` or the modhash.
- Do not vote, send private messages, evade bans, automate engagement, or
  cross-post identical content. This skill intentionally exposes none of those
  operations.
- Follow each subreddit's rules. Account age, karma and flair requirements can
  reject a post; report the rejection without exposing Reddit's raw authenticated
  response, which may contain reflected credential material.
- Do not retry a write automatically. A timeout may occur after Reddit accepted
  it, and replaying could create a duplicate.
- Respect rate limits and never bulk-submit. Use `r/test` only for a deliberate
  end-to-end validation.
- Cookie mode drives Reddit's first-party web JSON endpoints and may drift when
  Reddit changes its site. Report unexpected HTML or route errors as upstream
  drift instead of guessing another private endpoint.


## Record the output

After you successfully publish and obtain the live result URL, call the built-in
`publish_artifact` tool ONCE so the user can track this deliverable in **My Outputs**:

```
publish_artifact(kind="message", channel="reddit", title="<title>", url="<the REAL returned URL>", status="delivered")
```

Use the real returned URL — never fabricate one. Call it once per published item,
only after delivery is confirmed; skip it (or use `status="failed"`) if publishing failed.
See `_shared/artifacts.md`.
