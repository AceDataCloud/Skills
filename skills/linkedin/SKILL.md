---
name: linkedin
description: Publish text / link posts to your LinkedIn personal feed via the LinkedIn Posts API. Use when the user mentions LinkedIn, sharing or posting an update to LinkedIn, or cross-posting an article / link to their LinkedIn feed.
when_to_use: |
  Trigger when the user wants to publish a text or link share to their
  own LinkedIn feed. Posting is public on their profile — confirm the
  text (and link, if any) before publishing. Requires the
  w_member_social scope (granted by the connector at install).
connections: [linkedin]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Call the **LinkedIn API** with `curl + jq`. The user's bearer token is in
`$LINKEDIN_TOKEN`; every call needs `Authorization: Bearer $LINKEDIN_TOKEN`.

LinkedIn posts must be authored by the member's URN. Get the member id from the
OpenID userinfo endpoint, then build `urn:li:person:{sub}`.

```bash
SUB=$(curl -sS -H "Authorization: Bearer $LINKEDIN_TOKEN" \
  "https://api.linkedin.com/v2/userinfo" | jq -r .sub)
AUTHOR="urn:li:person:$SUB"
echo "$AUTHOR"
```

Errors are JSON with `message` / `serviceErrorCode` — show them verbatim.
`401` → token expired (tokens last ~60 days), re-connect the LinkedIn connector.

## Publish a post (Posts API)

**Confirm the text with the user first.** Use the versioned Posts API; set the
`LinkedIn-Version` header to a recent `YYYYMM` (LinkedIn requires a valid recent
version — if you get `426`/version errors, bump to the current month).

```bash
jq -n --arg a "$AUTHOR" --arg t "My update text. Check out https://studio.acedata.cloud" \
  '{author:$a, commentary:$t, visibility:"PUBLIC",
    distribution:{feedDistribution:"MAIN_FEED", targetEntities:[], thirdPartyDistributionChannels:[]},
    lifecycleState:"PUBLISHED", isReshareDisabledByAuthor:false}' \
| curl -sS -X POST "https://api.linkedin.com/rest/posts" \
    -H "Authorization: Bearer $LINKEDIN_TOKEN" \
    -H "Content-Type: application/json" \
    -H "LinkedIn-Version: 202401" \
    -H "X-Restli-Protocol-Version: 2.0.0" \
    -d @- -D - -o /dev/null | tr -d '\r' | awk '/^[Xx]-[Rr]estli-[Ii]d:|^[Ll]ocation:/{print}'
```

A successful create returns `201` with the post URN in the `x-restli-id`
(or `Location`) response header — report that URN / the resulting post URL.

> Link posts: put the URL inline in `commentary` (LinkedIn auto-unfurls it).
> Rich article attachments need the assets/images API — out of scope for a
> simple text/link share; keep links inline.

## Fallback: legacy ugcPosts

If the versioned endpoint is unavailable for the app, the older
`POST https://api.linkedin.com/v2/ugcPosts` with a
`specificContent."com.linkedin.ugc.ShareContent"` body also works with
`w_member_social`. Prefer `/rest/posts` above.

## Gotchas

- **Author URN** must match the token's member (`urn:li:person:{sub}`) — you
  can't post as someone else.
- `w_member_social` only allows posting to the **member's own feed**; company
  Page posts need `w_organization_social` + an admin role (not in this connector).
- The `LinkedIn-Version` header is mandatory for `/rest/*`; a stale value
  returns a version error — bump to the current `YYYYMM`.
