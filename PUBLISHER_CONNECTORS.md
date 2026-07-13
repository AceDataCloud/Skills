# Publisher Connectors — Go-Live Steps (what YOU need to do)

These connectors + skills are code-complete. Some need an OAuth app or API
enablement; Reddit works through ACE Cookie capture while its commercial OAuth
application is under review. After any platform setup, run
`python manage.py sync_connectors` (AuthBackend). Skills sync automatically via
the Skills catalog.

Common OAuth callback (Reddit & LinkedIn) — register the provider path below:

```
https://auth.acedata.cloud/oauth/callback/reddit
https://auth.acedata.cloud/oauth/callback/linkedin
```

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

## 3. Reddit — Cookie now; OAuth after Reddit approval

The recommended method is Cookie capture: log in to Reddit, then connect with
the ACE extension. No platform secret is required. The connector injects the
encrypted cookie jar as `REDDIT_COOKIES`; the skill can read identity / the
user's own submissions and submit confirmed text or link posts.

Official OAuth remains available as a second auth method, but Reddit now requires
explicit Data API approval before app registration. After written approval:

1. https://www.reddit.com/prefs/apps → **create app** → type **"web app"**.
2. **redirect uri** = `https://auth.acedata.cloud/oauth/callback/reddit`.
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
2. Connect Dev.to with an API key, Blogger/LinkedIn with OAuth, and Reddit with
   **Browser extension Cookie capture**. Reddit OAuth remains unavailable until
   Reddit grants written approval and production credentials are configured.
3. In Studio chat: "把这段发到我的 dev.to / Blogger / Reddit r/test / LinkedIn" →
   the matching skill runs with the injected credential and asks for explicit
   confirmation before posting.

## Cost note
Dev.to, Blogger and LinkedIn currently expose free API access for these flows.
Reddit commercial access is pending review and may require a separate agreement
or fees. X is pay-per-use, while Facebook needs app review and Page-token setup.
