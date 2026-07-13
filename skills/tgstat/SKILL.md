---
name: tgstat
description: "Research public Telegram channels and groups with TGStat. Use when discovering communities by topic, comparing public audience/reach/activity, checking a known @username, or shortlisting ad and outreach sources. The connector supplies TGSTAT_USERNAME as the default profile. Read-only: does not log in, join groups, scrape members, or send messages."
when_to_use: |
  Use for Telegram source discovery, competitor research, ad-channel
  selection, and public audience analysis. It can find channels/chats by
  keyword, inspect known public usernames, compare visible metrics, and use
  the connected Telegram username as the default target. Use the separate
  telegram connector for reading or sending messages in the user's account.
connections: [tgstat]
allowed_tools: [Bash, web_search, web_fetch]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "2.1"
---

# TGStat Research

Use [scripts/tgstat.py](./scripts/tgstat.py) for public TGStat research. It uses
only the Python standard library. Resolve the script at the start of every Bash
call because each call runs in a fresh shell:

```bash
TGSTAT="$SKILL_DIR/scripts/tgstat.py"; [ -f "$TGSTAT" ] || TGSTAT=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/tgstat.py' 2>/dev/null | head -1)
[ -f "$TGSTAT" ] || { echo "tgstat script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }
python3 "$TGSTAT" profile
```

The connector injects `$TGSTAT_USERNAME`. It is not a login credential; it is
only the default public channel/group target. Never print the full environment
or treat the username as proof that the user owns the Telegram account.

## Discover Sources by Topic

Run `search` first:

```bash
TGSTAT="$SKILL_DIR/scripts/tgstat.py"; [ -f "$TGSTAT" ] || TGSTAT=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/tgstat.py' 2>/dev/null | head -1)
[ -f "$TGSTAT" ] || { echo "tgstat script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }
python3 "$TGSTAT" search "Claude API" --type all --language English --country US
```

In public mode the command returns `web_queries`. Call `web_search` once per
query, then:

1. Keep only public `tgstat.com` regional-host and `t.me` results.
2. Extract public `@username` values and deduplicate case-insensitively.
3. Prefer results whose title/snippet directly matches the topic.
4. Verify each shortlist entry with `info` or `stat` before reporting it.
5. Include the source URL and say discovery may be incomplete because public
   search-engine indexes are not TGStat's full database.

TGStat's own keyword-search result endpoint requires sign-in. Do not try to
bypass it, replay private AJAX endpoints, or claim public mode searches the
full TGStat index.

`--language` and `--country` are search terms for the web index, not guaranteed
TGStat database filters.

## Browse Public Rankings

Use rankings when the user wants large or active public sources without a
precise keyword:

```bash
TGSTAT="$SKILL_DIR/scripts/tgstat.py"; [ -f "$TGSTAT" ] || TGSTAT=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/tgstat.py' 2>/dev/null | head -1)
[ -f "$TGSTAT" ] || { echo "tgstat script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }
python3 "$TGSTAT" rankings --type channel --limit 20
python3 "$TGSTAT" rankings --type chat --limit 20
python3 "$TGSTAT" rankings --type channel --query crypto --limit 10
```

Channel cards can expose subscribers, one-post reach, and citation index.
Chat cards can expose participants, recent message count, and MAU. Metrics are
a current public snapshot, not a historical series.

Public TGStat pages can intermittently return an authentication or rate-limit
interstitial. When `rankings` returns `status: unavailable`, try the emitted
`web_fetch_url`, then run its `web_queries` with `web_search`. Label those
results as web-index discoveries, not as an authoritative TGStat rank.

## Inspect a Known Channel or Group

Accept a public `@username`, bare username, `t.me/<username>` link, or a TGStat
entity URL. Omit the target to inspect `$TGSTAT_USERNAME` from the connector:

```bash
TGSTAT="$SKILL_DIR/scripts/tgstat.py"; [ -f "$TGSTAT" ] || TGSTAT=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/tgstat.py' 2>/dev/null | head -1)
[ -f "$TGSTAT" ] || { echo "tgstat script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }
python3 "$TGSTAT" info
python3 "$TGSTAT" info @durov
python3 "$TGSTAT" stat https://t.me/example_public_chat
```

In public mode, `info`/`stat` resolves whether the target is a channel or chat,
returns public metadata, and enriches it with ranking metrics when the entity
appears in the current public ranking. Empty metrics mean TGStat did not expose
them publicly; do not call that full statistics.

For ad selection, rank by relevant reach/activity rather than subscriber count
alone. High subscribers with weak reach or chat MAU can indicate an inactive or
inflated audience. Present metrics as evidence, not a guarantee of lead quality.

## Check the Connected Profile

```bash
TGSTAT="$SKILL_DIR/scripts/tgstat.py"; [ -f "$TGSTAT" ] || TGSTAT=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/tgstat.py' 2>/dev/null | head -1)
[ -f "$TGSTAT" ] || { echo "tgstat script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }
python3 "$TGSTAT" profile
```

`profile` reports the normalized public username used by target-less `info` and
`stat`. It does not verify ownership or authenticate to Telegram/TGStat.

## Outreach Research Workflow

For prospecting or partnership research:

1. Search several narrow problem/role keywords, not only broad `AI` terms.
2. Shortlist sources by relevance first, then audience/reach/activity.
3. Verify each public source and retain evidence URLs.
4. Label each source as channel, group/chat, or uncertain.
5. Produce a review queue with suggested angle and reason for fit.
6. Require human approval before any message is sent through another connector.

## Safety and Limits

- Read-only. This skill does not join channels/groups, import invite links,
  send messages, add members, or download member lists.
- Reject private invite links (`t.me/+...`, `joinchat/...`) and message links.
- Do not automate unsolicited bulk outreach or evade Telegram/TGStat controls.
- Public pages and HTML can change; if parsing fails, use `web_fetch` for a
  single public page and report only values visible in that page.
- Public web discovery is incomplete and regional TGStat pages may differ.
- Treat `$TGSTAT_USERNAME` as public profile context, not authentication.
