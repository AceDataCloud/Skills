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

Preserve the page on CAPTCHA, moderation, rate limit, account restriction, or unusual-activity warnings. Do not dismiss, solve, bypass, or retry around them.