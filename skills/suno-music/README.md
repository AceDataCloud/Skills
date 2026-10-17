# Suno by Ace Data Cloud — skills.sh first run

Use Suno through the **Ace Data Cloud** API from an Agent Skills-compatible coding assistant. This Skill is maintained by Ace Data Cloud and uses your Ace service API key; it does not claim to be published by Suno. Install it independently; the account Skill and an MCP server are optional.

[简体中文](readme.zh-CN.md) · [skills.sh installation page](https://skills.sh/acedatacloud/skills/suno-music) · [current models and pricing](https://platform.acedata.cloud/models?utm_source=skills_sh&utm_medium=referral&utm_campaign=evergreen&utm_content=suno_music_pricing)

## 1. Install this service only

Open the skills.sh page above and check the repository is **acedatacloud/skills**. In your project terminal:

```bash
npx --yes skills@1.7.2 add acedatacloud/skills --skill suno-music -a codex --yes
npx --yes skills@1.7.2 list
```

This example targets Codex; replace `codex` with your supported agent, such as `claude-code` or `cursor`. For Codex, the installed instructions are `.agents/skills/suno-music/SKILL.md`. Start a fresh session. Installation does not generate media or set up an API key. This is a Skill, not a model-provider dropdown or a new extension button.

For the released snapshot checked on 2026-10-18, use `https://github.com/AceDataCloud/Skills/tree/v2026.1017.279001` in place of `acedatacloud/skills`. That released snapshot predates these improved instructions; use the default branch after this PR is merged to receive them.

![Real skills.sh installation control](https://raw.githubusercontent.com/AceDataCloud/Skills/0901d63b7f7d216318463b1c33976838a084da3b/docs/skills-sh/installation-page-20261017.jpg)

Actual account-Skill page captured on 2026-10-17, showing the same installation control. Use this service's slug above; the screenshot is not a suno-music installation or generation result. [Image sources and limits](https://github.com/AceDataCloud/Skills/blob/0901d63b7f7d216318463b1c33976838a084da3b/docs/skills-sh/image-sources.json).

## 2. Register, sign in and get the correct API key

1. Open [Ace Data Cloud → Applications](https://platform.acedata.cloud/console/applications?utm_source=skills_sh&utm_medium=referral&utm_campaign=evergreen&utm_content=suno_music_api_key); register and sign in if needed.
2. Open **General application**. If absent, choose **Initialize General Application**. Check **Suno** access, current balance and price before submitting anything.
3. Copy the key on the application card, or open **Manage Keys → Create** to create a separate key such as `skills.sh Suno`. Set expiry and API/usage limits as needed. If **Allowed APIs** is enabled, include `/suno/audios` and `/suno/tasks`. Other actions in SKILL.md may need extra routes.
4. Copy only the key value. Do not include `Bearer ` or screenshot redaction characters. A `platform-...` management token is not the service key.

![Copy API key or open Manage Keys](https://raw.githubusercontent.com/AceDataCloud/SunoDify/8d3d03570e73324220f111f7fe343da0792a8071/_assets/tutorial/get-api-key-en.png)

![Create an optional dedicated key](https://raw.githubusercontent.com/AceDataCloud/SunoDify/8d3d03570e73324220f111f7fe343da0792a8071/_assets/tutorial/create-api-key-en.png)

These are existing, redacted **Ace console** screenshots from the [Suno Dify guide](https://github.com/AceDataCloud/SunoDify/blob/8d3d03570e73324220f111f7fe343da0792a8071/README.md), checked on 2026-10-18. They illustrate the shared key controls, not a Suno run in skills.sh. The example name “Dify tutorial” is illustrative; use your own name. Menu labels may change.

## 3. Put the key in the assistant's execution environment

skills.sh does not store credentials. For a terminal-launched coding assistant, export the key in that terminal **before starting the assistant**, then start a new session:

```bash
export ACEDATACLOUD_API_TOKEN="your_api_key_here"
```

For an already running IDE, restart it from the configured environment or use that IDE's documented secret/environment settings. A Skill install does not load `.env` automatically. Never paste the key into a prompt, commit it, or print it in logs. OpenClaw has its own Gateway setup in SKILL.md; it is not required for skills.sh installation.

## 4. Submit once and inspect the result

Read [SKILL.md](SKILL.md) and its exact request shape first. Ask your assistant to use **Suno by Ace Data Cloud**, inspect the current price, and prepare a single audio request using `chirp-v6`. Approve the intended cost before it submits `/suno/audios`. Installation and a prepared request do not prove that generation ran.

Run the existing Quick Start (the Generate section for GPT Image) only after the key and intended cost are correct. For an asynchronous response, save its task ID and query **that same ID** at `/suno/tasks`. Do not resubmit generation to check progress. Read the audio URL from the completed task result. A preview while pending is not a terminal result.

Example request copied from this Skill's current Quick Start. **Billable: run only after confirming the service, price and intended request.** It has not been executed for this guide:

```bash
curl -X POST https://api.acedata.cloud/suno/audios \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a happy pop song about coding", "model": "chirp-v6", "async": true}'
```

If the response returns a task ID, query that ID with the following command; replace `YOUR_TASK_ID` with the existing ID. A synchronous GPT Image result can already contain `data[].url` and does not need a task lookup:

```bash
curl -X POST https://api.acedata.cloud/suno/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id":"YOUR_TASK_ID"}'
```

The expected output is an actual returned audio/video/image URL after terminal success, not a URL copied from this guide. Keep the same task ID while pending.

Use the exact task response fields and terminal states in SKILL.md. A URL in this guide would be illustrative; no media generation was performed for this tutorial. Check the request/task history for one intended charge; a completed media link alone does not prove the final bill.

## Troubleshooting

| Symptom | What to check |
|---|---|
| 401 | Full service key, no `Bearer ` inside its value, available to the actual assistant process. |
| 403 | Service access, expiry and Allowed APIs; read the error because moderation can also return 403. |
| 400 | Exact model ID and request shape in SKILL.md; do not silently substitute a model. |
| 429 | Wait and reduce concurrency; do not automatically retry a paid submit. |
| Pending / timeout / 5xx | Read the same task or request history before considering a new submit. |
| Media URL unavailable | Confirm terminal success and use the actual returned URL; share only task/trace ID with support. |

Support: [dev@acedata.cloud](mailto:dev@acedata.cloud). Source: [AceDataCloud/Skills](https://github.com/AceDataCloud/Skills). skills.sh installation counters are not unique users or revenue. Source links use the four supported UTM fields for this skills.sh guide; they do not prove a registration or payment.
