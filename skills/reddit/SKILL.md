---
name: reddit
description: Search subreddits, read rules, reply to threads, and submit posts (link or text) to Reddit using either official OAuth or your own Reddit login cookies. Use when the user mentions Reddit, posting to a subreddit, replying or commenting on a thread, submitting a link or self-post, or checking their Reddit profile / submissions.
when_to_use: |
  Trigger when the user wants to find relevant Reddit threads, reply to a
  post or comment, submit a post to a subreddit (link or self/text post),
  or read their own Reddit identity and submissions. Commenting and posting
  are public and subject to that subreddit's rules / karma requirements —
  confirm the target and the exact text before writing.
connections: [reddit]
allowed_tools: [Bash, publish_artifact]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "2.1"
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
python3 "$R" comments --limit 10
```

`comment` verifies itself: when Reddit answers in a shape it cannot parse, it
looks the comment up via `comments` before reporting anything. If it still says
the write likely failed, re-check with `comments` yourself before resending.

## Find threads and check the rules

`search` returns each hit's `fullname` (`t3_…`), which is what `comment --parent`
takes. `subreddit-info` returns the subreddit's rules — **read them before
writing anything there.**

```sh
R="${SKILL_DIR:-}/scripts/reddit.py"; [ -f "$R" ] || R=$(find /tmp -maxdepth 8 -path '*/skills/*/reddit/scripts/reddit.py' -print -quit 2>/dev/null)
[ -f "$R" ] || { echo "reddit script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }

python3 "$R" search --query "suno api" --time week --limit 10
python3 "$R" search --query "image generation api" --subreddit SideProject
python3 "$R" subreddit-info --subreddit SideProject
```

`--sort` defaults to `relevance`. **Reddit's `new` sort ignores keyword relevance**
— it returns recent posts that often do not contain the query terms at all. Use
`--sort new` only to scan a specific subreddit's recent activity, never to find
threads by keyword.

## Reply to a thread — GATED

`--parent` accepts a fullname (`t3_…` post, `t1_…` comment) or a reddit.com
permalink. **Show the target thread and the exact reply text, then obtain
explicit confirmation.** Without a trailing `--confirm` this is a dry run.

```sh
R="${SKILL_DIR:-}/scripts/reddit.py"; [ -f "$R" ] || R=$(find /tmp -maxdepth 8 -path '*/skills/*/reddit/scripts/reddit.py' -print -quit 2>/dev/null)
[ -f "$R" ] || { echo "reddit script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }

python3 "$R" comment --parent t3_1r9yrtn --body-file reply.md
python3 "$R" comment --parent t3_1r9yrtn --body-file reply.md --confirm
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
- Do not vote, send private messages, evade bans, or cross-post identical
  content. This skill intentionally exposes none of those operations.
- **Never post the same reply text to more than one thread.** Reddit treats
  repeated identical comments as spam and actions the account, not the comment.
  Write each reply against the specific thread it answers.
- Follow each subreddit's rules — run `subreddit-info` first. Account age, karma
  and flair requirements can reject a post or comment; report the rejection
  without exposing Reddit's raw authenticated response, which may contain
  reflected credential material.
- Do not retry a write automatically. A timeout may occur after Reddit accepted
  it, and replaying could create a duplicate.
- Respect rate limits and never bulk-submit or bulk-comment. Use `r/test` only
  for a deliberate end-to-end validation.
- Cookie mode drives Reddit's first-party web JSON endpoints and may drift when
  Reddit changes its site. Report unexpected HTML or route errors as upstream
  drift instead of guessing another private endpoint.

## Self-promotion — read this before marketing anything

Reddit bans accounts for promotion patterns, not for individual links. When the
user's goal is promoting their own product:

- **Answer the question first.** A reply must stand on its own as useful even if
  the product link were removed. If it does not, do not send it.
- **Disclose the affiliation** ("I build X") — undisclosed promotion is the
  fastest route to a ban.
- **One link at most, at the end**, and never in a post title.
- **Do not blanket-reply.** A handful of genuinely relevant threads beats volume,
  and volume is exactly what spam detection keys on.
- If a subreddit has a dedicated self-promo / "Showoff" thread, use it — that is
  the sanctioned channel.
- A low-karma or new account will have posts auto-removed by AutoModerator in
  most active subreddits. Check `whoami` karma and warn the user rather than
  burning the account on a post that will be silently filtered.


## Record the output

After you successfully publish a post **or a comment** and obtain the live result
URL, call the built-in `publish_artifact` tool ONCE so the user can track this
deliverable in **My Outputs**:

```
publish_artifact(kind="message", channel="reddit", title="<title>", url="<the REAL returned URL>", status="delivered")
```

Use the real returned URL — never fabricate one. Call it once per published item,
only after delivery is confirmed; skip it (or use `status="failed"`) if publishing failed.
See `_shared/artifacts.md`.
