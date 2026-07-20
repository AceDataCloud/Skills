# Login and account session

## Status

1. Navigate or attach `https://www.xiaohongshu.com/explore` and wait up to 30 seconds in bounded intervals.
2. Treat a visible sidebar profile channel (`我` / profile link) as signed in. Treat a visible login prompt or QR container as signed out. URL alone is not sufficient unless it visibly redirects to login.
3. Determine login only from visible signed-in controls, profile links, or an explicit login prompt. Do not claim cryptographic account attestation.
4. If `browser.snapshot` is unavailable on the dense page, use `browser.screenshot` for this status check. If neither proves the state, ask the user to inspect the tab.

## QR login

1. Open the visible login control with a fresh ref or screenshot-bound point.
2. Read again. The upstream page contract renders the QR under the login container; call `browser.screenshot` and present the visible image, never the QR payload or session token.
3. The user scans locally. Poll every 500 ms only through bounded `browser.wait_for`/fresh observations, with a maximum matching the visible QR expiry (never more than 5 minutes).
4. Success requires the visible sidebar profile channel to appear. A disappeared QR alone is not success.
5. On expiry, ask before reopening a fresh QR. Never loop indefinitely.

## Switch or sign out

1. Show the visible current-account context and ask for explicit confirmation.
2. Use visible logout/switch controls with fresh refs after chat confirmation. Do not copy the upstream Cookie-deletion shortcut; this Skill never clears or exports Cookies.
3. Let the user complete credentials, SMS, QR, or verification locally.
4. Read again and report only the visible resulting account state.

There is deliberately no Cookie delete/export workflow. Never emulate `delete_cookies`.