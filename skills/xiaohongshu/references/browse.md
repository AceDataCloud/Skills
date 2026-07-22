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

Navigate to `https://www.xiaohongshu.com/` in the BrowserSession, then wait in 300 ms bounded intervals for feed cards to hydrate, for at most 8 seconds. Read the managed page. Scroll in bounded steps and read after each step. Return only the requested number of notes with title, author state, visible engagement, and canonical URL. Stop when enough results are collected, the page repeats, a warning appears, the 8-second hydration window expires without cards, or the user limit is reached.

## Search and filters

1. Normalize `{keyword, filters}` with `normalize-filters` before interacting. Supported filters are sort, note type, publish time, search scope, and location.
2. Navigate to `https://www.xiaohongshu.com/search_result?keyword=<encoded>&source=web_explore_feed`, or use the visible search control when the BrowserSession already has that page. Never invent a query token.
3. Wait for visible results. To filter, hover the visible `筛选` control, wait for the panel, then choose exact labels one group at a time in this order: sort, note type, publish time, search scope, location. Use the normalized labels from `normalize-filters` rather than positional guesses.
4. After every selection, wait for the panel/result state to settle and verify the exact selected label before continuing. If the hover panel closes, reacquire it; never click a stale option ref.
5. Return bounded cards. Never invent query tokens, counts, or hidden IDs.

## Detail and comments

Open a note from its fresh result ref or same-origin canonical URL. Prefer clicking the fresh feed link so any required page token remains browser-local. Retry navigation at most three times with a short bounded delay, then stop. Read visible text, media labels, author, engagement, and the first visible comment batch.

For more comments/replies, first scroll to the comment area. In each bounded round: expand at most three visible `展开 N 条回复` controls, read the count, scroll the last visible comment into view, then scroll about 70% of one viewport. Stop at the requested count, visible end marker, no-comment state, 20 stagnant rounds, warning, or caller limit. Never copy the upstream 500-attempt default into chat automation.

Pass the final semantic snapshot to `parse-note-snapshot --note-url <canonical-url>`. Preserve missing, ambiguous, and truncated states instead of filling absent fields. Only nodes with an explicit `comment` role are returned as structured comments; generic list items are never assumed to be comments.

## Profile

Open the fresh author link from a result/detail page. For the current account, use the sidebar `我` profile channel rather than fabricating an ID. Return visible profile text, followers/following/engagement totals, and bounded recent notes. Profile notes can be grouped/lazy-loaded; flatten only visibly observed note batches. Do not expose unrelated private account data.

Pass the final semantic snapshot to `parse-profile-snapshot --profile-url <canonical-url>` before reporting structured profile data. `visible_metrics` contains explicitly labeled profile metrics. Preserve `visible_counts` separately as unlabeled page counters; never reinterpret them as followers, following, likes, or favorites.

## Content planning

Search multiple user-approved keywords, compare recent and visibly high-engagement notes, inspect representative details/comments, and synthesize themes, title patterns, formats, audience questions, and tag opportunities. This workflow stays read-only unless the user separately requests publishing.