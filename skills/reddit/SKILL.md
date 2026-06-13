---
name: reddit
description: Submit posts (link or text) to subreddits and read your Reddit identity / content via the Reddit API. Use when the user mentions Reddit, posting to a subreddit, submitting a link or self-post, or checking their Reddit profile / submissions.
when_to_use: |
  Trigger when the user wants to submit a post to a subreddit (link or
  self/text post), or read their own Reddit identity and submissions.
  Posting to a subreddit is public and subject to that subreddit's rules
  / karma requirements — confirm the target subreddit, title and body
  before submitting.
connections: [reddit]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Call the **Reddit API** (OAuth endpoints) with `curl + jq`. The user's bearer
token is in `$REDDIT_TOKEN`. **Every call MUST send a `User-Agent` header** or
Reddit returns `429`. Use the OAuth host `https://oauth.reddit.com`.

```bash
UA="web:cloud.acedata.connectors:v1.0 (by /u/acedatacloud)"
```

Errors are JSON; a submit returns `{"json":{"errors":[...], "data":{...}}}` —
if `errors` is non-empty, show them verbatim. `401` → token expired, re-connect.

**Always start by confirming identity:**

```bash
curl -sS -H "Authorization: Bearer $REDDIT_TOKEN" -H "User-Agent: $UA" \
  "https://oauth.reddit.com/api/v1/me" | jq '{name, total_karma, link_karma}'
```

## Submit a post

**Confirm the subreddit + title + body with the user first.** `sr` is the
subreddit name WITHOUT the `r/` prefix.

```bash
# Self (text) post: kind=self + text. Link post: kind=link + url.
curl -sS -X POST "https://oauth.reddit.com/api/submit" \
  -H "Authorization: Bearer $REDDIT_TOKEN" -H "User-Agent: $UA" \
  --data-urlencode "sr=test" \
  --data-urlencode "kind=self" \
  --data-urlencode "title=My title" \
  --data-urlencode "text=My self-post body in markdown" \
  --data-urlencode "api_type=json" \
  | jq '.json | {errors, url: .data.url, id: .data.id}'
```

For a link post:

```bash
curl -sS -X POST "https://oauth.reddit.com/api/submit" \
  -H "Authorization: Bearer $REDDIT_TOKEN" -H "User-Agent: $UA" \
  --data-urlencode "sr=test" --data-urlencode "kind=link" \
  --data-urlencode "title=My title" --data-urlencode "url=https://example.com" \
  --data-urlencode "api_type=json" | jq '.json'
```

## Read my submissions

```bash
curl -sS -H "Authorization: Bearer $REDDIT_TOKEN" -H "User-Agent: $UA" \
  "https://oauth.reddit.com/user/USERNAME/submitted?limit=10" \
  | jq '.data.children[] | .data | {title, subreddit, ups, num_comments, permalink}'
```

## Gotchas

- **User-Agent is mandatory** on every request — omitting it → `429`.
- Many subreddits gate posting on **account age / karma / flair**; a submit can
  return `errors` like `[["SUBREDDIT_NOTALLOWED", ...]]` — surface it and try
  `r/test` to validate the flow.
- Respect rate limits: read the `X-Ratelimit-Remaining` response header; space
  out bulk submits.
- Use `r/test` as a safe target when validating that the connection works.
