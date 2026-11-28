# Ace Data Cloud skills for AnythingLLM

Install each skill separately in AnythingLLM Desktop or a self-hosted instance. Each skill ships a native `plugin.json` and `handler.js` and uses the token entered in its AnythingLLM settings.

| Skill | Capability | Source |
| --- | --- | --- |
| Google Search | Find web sources with structured organic Google results | [Google Search](skills/acedatacloud-google-search) |
| Suno | Check an existing task and retrieve available audio or lyrics | [Suno](skills/acedatacloud-suno) |

## Install from source

1. Copy the complete skill folder into `plugins/agent-skills/` inside your AnythingLLM storage directory. Keep the folder name and `hubId` identical.
2. Open **Settings → Agent Skills**, configure the skill, and enable it.
3. Run a prompt with `@agent` using the examples in the skill's guide.

[Get an API token](https://platform.acedata.cloud/console/applications?utm_source=github&utm_medium=referral&utm_campaign=evergreen&utm_content=anythingllm-skills) · [AnythingLLM custom skill guide](https://docs.anythingllm.com/agent/custom/introduction)

## Community Hub

The supported publishing path is the AnythingLLM Hub CLI with `upload --type agent-skill --path <skill-folder>` and a publisher Connection Key. Upload each folder independently. The Hub assigns the public import ID. Public visibility and the Hub's Verified badge are separate states.

[Community Hub upload](https://docs.anythingllm.com/community-hub/upload) · [Import and verification](https://docs.anythingllm.com/community-hub/faq#verification)
