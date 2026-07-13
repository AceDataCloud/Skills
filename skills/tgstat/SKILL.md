---
name: tgstat
description: "Research public Telegram channels and groups with TGStat. Use when discovering communities by topic, comparing audience size/reach/activity, checking a known @username, shortlisting ad or outreach sources, or querying TGStat API quota. Works without a TGStat login using web search plus public TGStat pages; an optional TGSTAT_TOKEN enables official structured search and full statistics. Read-only: does not join groups, scrape members, or send messages."
when_to_use: |
  Use for Telegram source discovery, competitor research, ad-channel
  selection, and public audience analysis. It can find channels/chats by
  keyword, inspect known public usernames, compare ranking metrics, and
  check optional TGStat API quota. Use the separate telegram connector for
  reading or sending messages in the user's own account.
connections: [tgstat]
allowed_tools: [Bash, web_search, web_fetch]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "2.0"
---

# TGStat Research

Use [scripts/tgstat.py](./scripts/tgstat.py) for public TGStat pages and the
optional official API. It uses only the Python standard library.

```bash
TGSTAT="$SKILL_DIR/scripts/tgstat.py"; [ -f "$TGSTAT" ] || TGSTAT=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/tgstat.py' 2>/dev/null | head -1)
[ -f "$TGSTAT" ] || { echo "tgstat script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }
python3 "$TGSTAT" mode
```

The connector has two modes:

- **Public research (default):** no TGStat account or token. Uses `web_search`
  for discovery and public TGStat ranking/entity pages for verification.
- **TGStat API Token (optional):** when the connector injects
  `$TGSTAT_TOKEN`, the same commands automatically use the official Stat API.

Commands default to `--access-mode auto`. Use `--access-mode public` before the
subcommand when a configured Token lacks access to a paid API method; use
`--access-mode api` to require API mode and fail clearly if no Token exists.

Never ask the user to paste a token into chat or pass it on the command line.
If they want API mode, ask them to add the Token through the TGStat connector.

## Discover Sources by Topic

Run `search` first:

```bash
TGSTAT="$SKILL_DIR/scripts/tgstat.py"; [ -f "$TGSTAT" ] || TGSTAT=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/tgstat.py' 2>/dev/null | head -1)
[ -f "$TGSTAT" ] || { echo "tgstat script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }
python3 "$TGSTAT" search "Claude API" --type all --language english --country us
python3 "$TGSTAT" --access-mode api search --category technology --type channel
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

Official API mode also supports category-only search. Category values are
TGStat reference keys; if a key is rejected, query the user's intended topic by
keyword in public mode instead of guessing another category.

With `$TGSTAT_TOKEN`, `search` calls the official `channels/search` endpoint
instead. That endpoint may require a paid Stat API plan. `--language` must be a
TGStat language key such as `english` or `russian`; `--country` must be a
two-letter country code such as `us` or `ru`.

If API search reports plan access denied, rerun explicitly in public mode:

```bash
python3 "$TGSTAT" --access-mode public search "Claude API" --type all
```

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

Accept only a public `@username`, bare username, `t.me/<username>` link, or a
TGStat entity URL:

```bash
TGSTAT="$SKILL_DIR/scripts/tgstat.py"; [ -f "$TGSTAT" ] || TGSTAT=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/tgstat.py' 2>/dev/null | head -1)
[ -f "$TGSTAT" ] || { echo "tgstat script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }
python3 "$TGSTAT" info @durov
python3 "$TGSTAT" stat https://t.me/example_public_chat
```

In public mode, `info`/`stat` resolves whether the target is a channel or chat,
returns public metadata, and enriches it with ranking metrics when the entity
appears in the current public ranking. Empty metrics mean TGStat did not expose
them publicly; do not call that full statistics.

With `$TGSTAT_TOKEN`:

- `info` uses `channels/get` for structured identity/category metadata.
- `stat` uses `channels/stat` for fuller channel reach/ER or chat activity.

For ad selection, rank by relevant reach/activity rather than subscriber count
alone. High subscribers with weak reach or chat MAU can indicate an inactive or
inflated audience. Present metrics as evidence, not a guarantee of lead quality.

## Check API Mode and Quota

```bash
TGSTAT="$SKILL_DIR/scripts/tgstat.py"; [ -f "$TGSTAT" ] || TGSTAT=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/tgstat.py' 2>/dev/null | head -1)
[ -f "$TGSTAT" ] || { echo "tgstat script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }
python3 "$TGSTAT" mode
python3 "$TGSTAT" quota
```

Without a Token, `quota` returns `null`. With a Token it calls `usage/stat`.
If TGStat reports an inactive plan or insufficient access, explain that the
public workflow still works and that API search/full stats depend on the user's
TGStat plan.

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
- Never print `$TGSTAT_TOKEN`, include it in reports, or expose command errors
  containing secrets.
