# Login and account session

## Status

1. Attach `https://www.xiaohongshu.com` and call `browser.read_page` with that exact origin.
2. Determine login only from visible signed-in controls, profile links, or an explicit login prompt. Do not claim cryptographic account attestation.
3. If the state is ambiguous or the snapshot is truncated before account controls, ask the user to inspect the tab.

## QR login

1. Open the visible login control with a fresh ref and local approval.
2. Read again. If a QR is present, call `browser.screenshot` and present the image; never extract QR payloads or session tokens.
3. The user scans locally. Wait in bounded intervals and read again until a visible signed-in state appears or the QR expires.
4. On expiry, ask before reopening a fresh QR. Never loop indefinitely.

## Switch or sign out

1. Show the visible current-account context and ask for explicit confirmation.
2. Use visible logout/switch controls with fresh refs and local approval.
3. Let the user complete credentials, SMS, QR, or verification locally.
4. Read again and report only the visible resulting account state.

There is deliberately no Cookie delete/export workflow. Never emulate `delete_cookies`.