# Veo

![Veo service icon](assets/service-icon.png)

[简体中文](readme/README_zh_Hans.md) · Version 0.1.0

Create Veo videos from text or image frames and retrieve results through Ace Data Cloud. This independent Claude Code plugin is maintained by Ace Data Cloud.

## Install

Install [uv](https://docs.astral.sh/uv/) so `uvx` is available to Claude Code. Then install only this service:

```text
/plugin marketplace add AceDataCloud/Skills
/plugin install veo@acedatacloud-skills
```

Open [Applications](https://platform.acedata.cloud/console/applications?utm_source=github&utm_medium=referral&utm_campaign=evergreen), [locate the application](assets/get-api-key-en.png), and [create a dedicated key](assets/create-api-key-en.png) for Veo. Enter the raw token in the plugin's masked **Ace Data Cloud API Token** setting. Keep it out of prompts and project files.

## First use

Ask for the supported Veo models. `veo_list_models` reads the built-in reference from the [pinned MCP package](https://pypi.org/project/mcp-veo/2026.11.27.0/) without submitting a job. For a requested generation, use `veo_text_to_video` for text or `veo_image_to_video` for reference images. For image-to-video, use the number and order of reference frames required by the chosen model. Consult the built-in prompt guide for model-specific options. Generation consumes credits. Review [current pricing](https://platform.acedata.cloud/models?utm_source=github&utm_medium=referral&utm_campaign=evergreen) before submitting, keep the task ID, and use `veo_get_task` to check that same task.

[Support](https://platform.acedata.cloud/support?utm_source=github&utm_medium=referral&utm_campaign=evergreen)
