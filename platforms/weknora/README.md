# Ace Data Cloud in WeKnora

[中文指南](README.zh-CN.md) · [WeKnora's Skills guide](https://weknora.weixin.qq.com/docs/03-features/22-skills-sandbox) · [WeKnora's MCP guide](https://weknora.weixin.qq.com/docs/03-features/08-mcp)

The latest stable release checked on 2026-10-15 is [WeKnora **v0.8.3**](https://github.com/Tencent/WeKnora/releases/tag/v0.8.3). The UI walkthrough and dated Agent examples below were captured with v0.8.2; they have not been repeated end to end on v0.8.3. WeKnora can import public ClawHub, SkillHub, Git, and ZIP skills and connect Streamable HTTP MCP servers. The released v0.8.2 Toolbox has no remote marketplace search or service-list search field. A later development build adds filtering of items already registered in the workspace, which still does not search remote registries. For a first real call, use the hosted Suno MCP server below. A Skill supplies instructions; an MCP server supplies callable tools.

**Lite version note:** v0.8.2 omits the SQLite MCP metadata migration, so adding a service can fail with `table mcp_services has no column named usage_instructions` ([upstream issue #4058](https://github.com/Tencent/WeKnora/issues/4058)). The merged fix [#4060](https://github.com/Tencent/WeKnora/pull/4060) is included in v0.8.3. Start with v0.8.3 or a later compatible release; do not hand-edit a production database. On 2026-10-15, the unmodified v0.8.3 source passed the fresh SQLite schema and v33 MCP-preserving upgrade tests, plus the complete database package suite. This verifies the migration tests, not a new UI installation or Agent run. The v0.8.2 screenshots used a separate disposable database with the upstream migration applied.

## 1. Get an Ace Data Cloud key

1. Sign in to the [Ace Data Cloud console](https://platform.acedata.cloud/console/applications?utm_source=weknora&utm_medium=integration&utm_campaign=agent-onboarding), acquire the **Suno** service, and create a credential with Suno access. If you also add a chat model in WeKnora, that credential needs **AI Chat** access too.
2. Check the [current Suno pricing](https://platform.acedata.cloud/services/suno?tab=pricing&utm_source=weknora&utm_medium=integration&utm_campaign=agent-onboarding) and available Credits before generation. A generation is billable; task lookups are separate reads.
3. Keep the key private. Enter it only in WeKnora's credential field. Do not put it in a chat prompt, JSON example, screenshot, or Git commit.

## 2. Import the Suno MCP service

1. In WeKnora, open **Toolbox → MCP Services → Add Service**. Choose **Import from code** and paste [suno.mcp.json](suno.mcp.json), or enter the name `Suno`, URL `https://suno.mcp.acedata.cloud/mcp`, and transport **Streamable HTTP** manually. The sample contains no credential.
2. In authentication, select **Bearer Token** if that is the label in your version. If the form shows **API Key / Token**, set header name `Authorization` and credential value `Bearer <your Ace key>`. Do not place the key under ordinary custom headers.
3. Save and run **Test Connection**. Sync tools, then confirm `suno_generate_music`, `suno_get_task`, and `suno_list_models` are present. Keep just the tools you intend the agent to use enabled. Enable call approval for generation if your workspace requires it.
4. In your Agent editor, enable MCP access and select the Suno service. Save the Agent, then start a new **Smart Reasoning** conversation. A saved service that is not selected by the Agent is not usable in its chat.

![WeKnora v0.8.2 MCP authentication form with the Suno URL, Authorization header, and an empty secret field](assets/suno-mcp-auth-v082.jpg)

![Suno MCP card with 42 synchronized tools in the English Toolbox](assets/suno-mcp-v082.jpg)

These are real English UI captures from the isolated v0.8.2 frontend and an isolated SQLite database with upstream migration #4060 applied. No key is shown.

The hosted endpoint requires a Bearer credential: an unauthenticated request returns 401. With an authorized Ace key, the MCP `initialize` and `tools/list` calls succeeded on 2026-10-11; `suno_list_models` returned the current model list. These checks establish connection and discovery, not a completed paid song.

Before generating, ask the Agent: **“Call only `suno_list_models` and return the model IDs; do not generate music.”** This verifies the tool path without a Suno generation charge. The Agent's chat model can still incur its own usage.

## 3. Generate and retrieve one song

In the Agent chat, ask:

> Use the Suno MCP service to create one short instrumental track about a quiet morning. Use a model currently listed by `suno_list_models`. Make one `suno_generate_music` call, save its `task_id`, then call `suno_get_task` with that same ID until `state` is `complete` and `success` is true. Return the final `audio_url` and task ID. Do not submit a second generation while waiting.

The generation tool returns quickly with a task ID. `pending` or an HTTP 200 means the job was accepted, not that the audio is finished. Continue querying the **same** task ID after a timeout or interruption. Open the returned final audio URL to verify the file plays. In the Ace Data Cloud console, compare the one generation with its usage record and charged Credits; use the current package rate if converting Credits to USD.

If you only need a completed older task, ask the Agent to call `suno_get_task` with its saved ID. This checks retrieval without paying for another generation.

![A WeKnora v0.8.2 Agent calls Suno List Models and returns current model IDs](assets/suno-agent-list-models-v082.jpg)

This UI run called the free `suno_list_models` tool on the patched stable-source test database; it did not submit another song.

### Verified example (2026-10-11)

An isolated local WeKnora Lite build with the Ace model-provider branch connected to Suno MCP, enabled `suno_generate_music` with one-call approval, and submitted exactly one `chirp-v6-mini` instrumental generation. The returned task ID was `938109ac-c2b8-4cdd-9c0d-2bf8cf66b4be`. A later WeKnora Agent `suno_get_task` call on that **same ID** returned `state=complete`, `response.success=true`, and two `succeeded` outputs: [audio 1](https://cdn.acedata2.cloud/suno/1afac1aa-c215-4f54-a899-7c2a8ee6ea37.mp3) and [audio 2](https://cdn.acedata2.cloud/suno/9b2813f0-03ac-44bb-ba38-cc00a5513f93.mp3). Both URLs returned HTTP 200 with `audio/mpeg`. A matching Ace usage record for this trace shows **0.56 Credits original, 0.504 Credits deducted** under the test account's discount. Browser playback was not verified. This is a local development build result; it does not establish stable-release or marketplace availability.

## 4. Add a Skill when you need instructions

For the server deployment described here, have a workspace Admin/Owner configure a working sandbox in **Settings → Sandbox Config**. If the list is empty, a Skill can be registered but cannot be installed or run. The hosted MCP path above does not require a Skill sandbox.

Workspace Admin/Owner can open **Toolbox → Skills → Add Skill** and paste the public source `https://github.com/AceDataCloud/Skills/tree/main/skills/suno-music`. Choose a configured sandbox and wait for its install status to become **Ready**. Configure the skill's declared `ACEDATACLOUD_API_TOKEN` privately if it executes shell commands. Then select the skill and sandbox in the Agent editor. Adding a catalog entry alone does not install it; installing a Skill alone does not add MCP tools.

![The Suno Skill is registered in the English workspace catalog but not installed on any sandbox](assets/suno-skill-catalog-v082.jpg)

You can [search Suno on skills.sh](https://www.skills.sh/search?q=suno) and see the `acedatacloud/skills` listing and install command. In the v0.8.2 test, pasting the **skills.sh page URL** into WeKnora returned `Skill not found` because its resolver requires a ClawHub federated copy ([upstream issue #4167](https://github.com/Tencent/WeKnora/issues/4167)). Paste the GitHub skill-directory URL above instead; it registered as `suno-music` in the isolated stable-source test. That is a manual source import, not in-product marketplace search or a completed sandbox install.

WeKnora also resolves ClawHub/SkillHub pages and slugs, but external listings may lag the current [Ace Skills source](https://github.com/AceDataCloud/Skills). Check the skill contents and version before installing. The v0.8.2 Toolbox did not offer remote marketplace search. The proposed [chat discovery and install feature #3409](https://github.com/Tencent/WeKnora/pull/3409) is still open as checked on 2026-10-15; it is separate from SQLite migration #4060. Pasting a source remains the documented manual path; this guide does not establish official marketplace installation.

## 5. Other named services

Use the same Skill source pattern for each service below, replacing `suno-music` with its skill ID. Each linked `SKILL.md` gives the service's operation and task-query contract. Where a hosted MCP endpoint is in the [MCP mapping](../../skills/_shared/mcp-servers.md), connect it in **Toolbox → MCP Services** with the same private Bearer credential and select its specific tools. Verify the actual server tool list and a final result before treating a service as working in WeKnora.

| Service users search for | Skill ID |
| --- | --- |
| Suno | [suno-music](../../skills/suno-music/SKILL.md) |
| GPT Image | [gpt-image-2-5](../../skills/gpt-image-2-5/SKILL.md) |
| Seedance | [seedance-video](../../skills/seedance-video/SKILL.md) |
| Fish Audio | [fish-audio](../../skills/fish-audio/SKILL.md) |
| Seedream | [seedream-image](../../skills/seedream-image/SKILL.md) |
| Happy Horse | [happyhorse-video](../../skills/happyhorse-video/SKILL.md) |
| Qwen Image | [qwen-image](../../skills/qwen-image/SKILL.md) |
| Veo | [veo-video](../../skills/veo-video/SKILL.md) |
| Google Search | [google-search](../../skills/google-search/SKILL.md) |
| Grok Video | [grok-video](../../skills/grok-video/SKILL.md) |
| Face Transform | [face-transform](../../skills/face-transform/SKILL.md) |
| Midjourney | [midjourney-image](../../skills/midjourney-image/SKILL.md) |
| Flux | [flux-image](../../skills/flux-image/SKILL.md) |
| MiniMax H3 | [minimax-video](../../skills/minimax-video/SKILL.md) |
| Wan | [wan-video](../../skills/wan-video/SKILL.md) |
| Kling | [kling-video](../../skills/kling-video/SKILL.md) |
| Nano Banana | [nano-banana-image](../../skills/nano-banana-image/SKILL.md) |

![Seventeen named MCP services configured in an isolated WeKnora v0.8.2 workspace](assets/seventeen-mcp-cards-v082.jpg)

The 17 service cards were each connected and synchronized through the WeKnora backend with the upstream SQLite migration applied to this disposable test database. This is the workspace's configured list, **not** a remote marketplace. Cards use WeKnora's generic tool icon; per-service logos are not shown in this UI. A synchronized tool list is not proof that each paid generation completed.

### Verified GPT Image 2.5 example (2026-10-12)

With a credential authorized for GPT Image and after checking the current [image API price](https://platform.acedata.cloud/api/v1/apis/?path=%2Fopenai%2Fimages%2Fgenerations&utm_source=weknora&utm_medium=integration&utm_campaign=agent-onboarding), an Agent in the same isolated patched v0.8.2 instance selected the **GPT Image** MCP service. Only image generation, image task retrieval, and the image model list were enabled; generation required one-call approval. One `openai_generate_image` call used `gpt-image-2.5-flare`, `1024x1024`, `quality=low`, `n=1`, and `async=true`. The Agent queried task `496c8575-2cbc-4c84-b20e-c732f4d4764c` twice: first pending, then `finished_at` with `response.success=true`. The [final image](https://cdn.acedata2.cloud/gpt-image/a8aee29222a3b4e2c4dcb7c3ad585d00ef57359b456efc1dbf177b19da19f40e.png) opened at 1024×1024 and visually matched the white-cup prompt. A single matching usage record shows **0.19 Credits original, 0.171 Credits deducted**. No second image generation was submitted.

![GPT Image 2.5 Flare result displayed inside the real English WeKnora chat](assets/gpt-image-2-5-agent-v082.jpg)

This verifies GPT Image's manually configured MCP path in the patched stable-source test instance. It does not verify WeKnora marketplace discovery, unmodified Lite v0.8.2, or the other 15 services' main actions.

For chat models in the tested v0.8.2 UI, use **Settings → Models → Add Model → Chat → API → Custom (OpenAI-compatible)**, base URL `https://api.acedata.cloud/v1`, a documented chat model ID such as `gpt-4.1-mini`, and an Ace key with AI Chat access. Test Connection before saving. A named Ace Data Cloud provider is [under upstream review](https://github.com/Tencent/WeKnora/pull/4163); its source PR and CI are not an installed stable release.

![Preview of the named Ace Data Cloud Provider and GPT-4.1 Mini catalog entry in the development build](assets/ace-model-provider-preview.jpg)

The preview uses the v0.8.2 frontend against the development backend from that PR. The logo is the original Ace brand PNG; this option is absent from the unmodified stable backend.

## Troubleshooting

- **Cannot search Suno before adding it:** v0.8.2 has no remote marketplace search in the Toolbox and no service-list search field in the observed stable UI. Add the MCP URL or Git Skill source directly. Later development builds filter only already registered workspace items.
- **401 / 403:** Check that the stored credential has the `Authorization: Bearer` form and Suno permission. A 403 can also be content moderation; inspect the returned message.
- **429:** Respect the reported rate limit. **5xx or connection interruption:** keep the original `task_id` and query it before any new generation.
- **Tool exists but is never called:** Check that the Agent uses Smart Reasoning, has MCP enabled, selects Suno, and has the needed tool enabled. A disabled tool or unselected service is not callable.
- **Task ID with no playable audio:** Continue querying until terminal `state=complete` and `success=true`; inspect the final URL and open it. Do not present the task ID as the artifact.
- **Skill remains unavailable:** Check its sandbox install status and the Agent's selected sandbox and skill scope. Rebuilding a sandbox can temporarily change availability.
- **skills.sh page returns `Skill not found`:** Use the GitHub skill-directory source shown in step 4. WeKnora's current skills.sh resolver only covers listings federated to ClawHub; [#4167](https://github.com/Tencent/WeKnora/issues/4167) tracks the remaining gap.
