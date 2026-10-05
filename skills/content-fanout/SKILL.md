---
name: content-fanout
description: Adapt one canonical technical source into reviewed drafts for explicitly named connected channels, publish only selected targets, and collect verified URLs with channel attribution.
when_to_use: |
  Use when the user supplies a source article or release and names at least two
  target channels. This is a supervised distribution workflow, not a scheduled
  mass-posting service.
allowed_tools: [Bash, publish_artifact]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# Supervised content fan-out

## Inputs

Require a canonical source URL or complete source text, a campaign ID, and an
**explicit** target list. Never expand `all platforms` into every connector.
Read the conversation's authoritative `<connectors>` and `<skills>` blocks to
identify active publishing skills. For an unconnected target, list its
connection link and leave it pending; never guess a skill slug or call an
unconnected loader.

## Prepare

1. Extract verifiable claims, links, media rights, product availability, and
   a single canonical destination. Drop unsupported performance claims.
2. Produce a channel-specific draft and an attributed link for each target:
   `utm_source=<channel>&utm_medium=<medium>&utm_campaign=<campaign>`.
   Use `social` for social/community posts and `referral` for developer
   directories and syndicated technical articles; use the campaign contract's
   registered source mapping when one exists.
   Preserve any existing query parameters. Keep a separate draft for each
   language and audience; do not copy an identical body everywhere.
3. Present a table with target account, title, complete text, link, attachment,
   and proposed visibility. Ask the user to select exact targets and review
   the final drafts before public writes.

## Publish and verify

Load each target's existing skill one at a time and follow its own official
API, confirmation, and readback rules. A loaded skill can narrow the active
tool set; `load_skill` remains available for switching. Send one target at a
time and record the returned ID or URL. On timeout, 5xx, or ambiguous result,
read the target account's recent posts before any retry. Do not issue a second
write merely because the first response was lost.

Use `publish_artifact` once for each **verified** public URL. Report these
states separately: `draft`, `submitted`, `verified`, `failed`, and `pending`.
This workflow has no durable cross-run dedup database, so it must stay
supervised; a scheduled service must add persistent `source_id + channel +
content_hash` idempotency before unattended use.

For Reddit, Hacker News, Product Hunt, and Habr, prepare platform-native drafts
for manual review. Do not automate community submissions or bypass platform
publication rules. For LinkedIn, X, TikTok, Instagram, and other reviewed
APIs, public automation is available only after the actual app permissions
are active and the target skill proves a verified result.
