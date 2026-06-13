# Publisher Connectors — Go-Live Steps (what YOU need to do)

These connectors + skills are code-complete. To make them **work on production**,
a human has to register OAuth apps / enable APIs and set secrets, then run the
sync commands. Per-platform steps below. Order: do the setup, set the env, then
`python manage.py sync_connectors` (AuthBackend) — the skills sync automatically
via the Skills catalog.

Common OAuth callback (Reddit & LinkedIn) — register **the same redirect base
the existing Google/GitHub connectors use**, with the provider path appended:

```
https://auth.acedata.cloud/api/v1/connections/callback/reddit
https://auth.acedata.cloud/api/v1/connections/callback/linkedin
```
(If your Google/GitHub apps use a different callback base, mirror it — the path
segment is the provider id `reddit` / `linkedin`.)

---

## 1. Dev.to — nothing for you to do ✅
BYOC. Each end-user generates their own key at
**dev.to → Settings → Extensions → "DEV Community API Keys" → Generate API Key**
and pastes it into the connector. No platform-side setup, no secret.

## 2. Blogger — enable an API on the existing Google app
No new OAuth app (reuses your Google client, same as Drive/Gmail/YouTube):
1. Google Cloud Console → the project behind `GOOGLE_OAUTH_CLIENT_ID` → **APIs & Services → Library → enable "Blogger API v3"**.
2. OAuth consent screen → **add scope** `https://www.googleapis.com/auth/blogger`.
   (It's a sensitive scope → may need Google verification, like youtube.upload.)
3. No new env var needed.

## 3. Reddit — register an OAuth app
1. https://www.reddit.com/prefs/apps → **create app** → type **"web app"**.
2. **redirect uri** = the Reddit callback above.
3. Copy the client id (under the app name) + secret.
4. Set K8s secret env on AuthBackend:
   - `REDDIT_OAUTH_CLIENT_ID=...`
   - `REDDIT_OAUTH_CLIENT_SECRET=...`

## 4. LinkedIn — register an app + add products
1. https://www.linkedin.com/developers/apps → **Create app** (needs a Company Page).
2. **Products** tab → request **"Sign In with LinkedIn using OpenID Connect"** + **"Share on LinkedIn"** (the latter grants `w_member_social`).
3. **Auth** tab → add the LinkedIn redirect uri above.
4. Copy Client ID + Client Secret → set on AuthBackend:
   - `LINKEDIN_OAUTH_CLIENT_ID=...`
   - `LINKEDIN_OAUTH_CLIENT_SECRET=...`

---

## After setup (per deploy)
```bash
# AuthBackend pod — upsert the connector directory rows (idempotent)
python manage.py sync_connectors
```
The 4 skills (devto / blogger / reddit / linkedin) ship in AceDataCloud/Skills and
are pulled into the Skill catalog by the normal skills sync; each connector's
`required_skills` auto-installs its skill on connect.

## Verify it works (online)
1. Open **auth.acedata.cloud → Browse connectors** → the 4 new cards appear.
2. Click **Connect** on Dev.to (paste a key) and on Blogger/Reddit/LinkedIn (OAuth).
3. In Studio chat: "把这段发到我的 dev.to / Blogger / Reddit r/test / LinkedIn" →
   the matching skill runs with the injected token and posts.

## Cost note
Dev.to, Blogger, Reddit, LinkedIn — all free APIs. (We deliberately skipped X,
which is now pay-per-use $0.01/post, and Facebook, which needs app review +
Page-token complexity.)
