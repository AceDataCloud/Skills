# Browse, search, detail, profile, and planning

## Feed-card contract

Apply this only on `https://www.xiaohongshu.com` recommendation, search, or profile-note lists:

1. A card starts at a named same-origin link whose path is exactly `/explore/<alphanumeric-note-id>`. Empty-name links and reserved paths never start cards.
2. Its bounded range ends immediately before the next named valid note link.
3. Assign an author only when exactly one named same-origin `/user/profile/<alphanumeric-user-id>` link occurs in that range. Otherwise report `unavailable` or `ambiguous`.
4. A section may concatenate title, author, and engagement. Never replace the named link title/author with aggregate text.
5. Name a metric only when a visible label/control identifies it. Otherwise return an unlabeled visible engagement value.
6. Do not use this heuristic on creator pages or unfamiliar page types. Stop instead of inventing cards or IDs.

Use `parse-feed-snapshot` when a machine-checked card list is useful. Preserve `truncated=true` in the answer.

## Recommendations

Read the attached home/recommendation page. Scroll in bounded steps and read after each step. Return only the requested number of notes with title, author state, visible engagement, and canonical URL. Stop when enough results are collected, the page repeats, a warning appears, or the user limit is reached.

## Search and filters

1. Normalize `{keyword, filters}` with `normalize-filters` before interacting. Supported filters are sort, note type, publish time, search scope, and location.
2. Read the current page, open the search control, fill the exact keyword, and submit with a fresh visible control or supported key.
3. Read the result page. Apply requested filters one at a time using fresh refs and verify each visible selected state.
4. Return bounded cards. Never invent query tokens, counts, or hidden IDs.

## Detail and comments

Open a note from its fresh result ref or same-origin canonical URL. Read visible text, media labels, author, engagement, and the first visible comment batch. For more comments/replies, expand and scroll in bounded batches, reading after every transition and stopping at the requested limit. This is not a guaranteed full-comment export.

Pass the final semantic snapshot to `parse-note-snapshot --note-url <canonical-url>`. Preserve missing, ambiguous, and truncated states instead of filling absent fields. Only nodes with an explicit `comment` role are returned as structured comments; generic list items are never assumed to be comments.

## Profile

Open the fresh author link from a result/detail page. Return visible profile text, followers/following/engagement totals, and bounded recent notes. Do not expose unrelated private account data.

Pass the final semantic snapshot to `parse-profile-snapshot --profile-url <canonical-url>` before reporting structured profile data. Report only explicitly labeled profile metrics; never reinterpret unrelated page numbers as followers, following, likes, or favorites.

## Content planning

Search multiple user-approved keywords, compare recent and visibly high-engagement notes, inspect representative details/comments, and synthesize themes, title patterns, formats, audience questions, and tag opportunities. This workflow stays read-only unless the user separately requests publishing.