# Reconciliation after uncertain browser writes

Use this after timeout, disconnect, stale ref, navigation, an ambiguous result, or any error after a write may have started.

1. Do not repeat the write.
2. Read the exact expected origin again using fresh refs.
3. Classify the outcome:
   - `succeeded`: the exact intended state is visible (reaction state, exact comment/reply, uploaded media, filled preview, publish success, scheduled item, or canonical destination).
   - `not_applied`: the previous state is clearly visible and no warning/error/processing state remains.
   - `unknown`: neither state is conclusive, the snapshot is truncated at the relevant area, the tab detached, or a warning/challenge is present.
4. If `succeeded`, report success without another action.
5. If `not_applied`, reversible actions may be attempted once from the verified state. Irreversible actions require a fresh preview and renewed chat confirmation.
6. If `unknown`, stop and ask the user to inspect the local tab. Never retry publish, schedule, comment, or reply while unknown.

Action-specific success signals benchmarked from the local-browser workflow:

- Image upload: preview count reaches the submitted image count; a file-input event alone is not success.
- Video upload: Publish becomes enabled after processing; file selection alone is not success.
- Publish/schedule: URL leaves `/publish/publish` or a visible success destination appears within 15 seconds.
- Comment/reply: the exact submitted text renders in the comments area within 4 seconds.
- Like/favorite: the visible/semantic state equals the requested boolean; click completion alone is not success.

Preserve the page on CAPTCHA, moderation, rate limit, account restriction, or unusual-activity warnings. Do not dismiss, solve, bypass, or retry around them.