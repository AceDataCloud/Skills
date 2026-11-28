# Kling

![Kling service icon](assets/service-icon.png)

[简体中文](readme/README_zh_Hans.md) · Version 0.1.0

Create Kling videos from text or a reference image and retrieve results through Ace Data Cloud. This independent Claude Code plugin is maintained by Ace Data Cloud.

## Install

Install [uv](https://docs.astral.sh/uv/) so `uvx` is available to Claude Code. Then install only this service:

```text
/plugin marketplace add AceDataCloud/Skills
/plugin install kling@acedatacloud-skills
```

Open [Applications](https://platform.acedata.cloud/console/applications?utm_source=github&utm_medium=referral&utm_campaign=evergreen), [locate the application](assets/get-api-key-en.png), and [create a dedicated key](assets/create-api-key-en.png) for Kling. Enter the raw token in the plugin's masked **Ace Data Cloud API Token** setting. Keep it out of prompts and project files.

## First use

Ask for the supported Kling models. `kling_list_models` reads the built-in reference from the [pinned MCP package](https://pypi.org/project/mcp-kling/2026.11.27.0/) without submitting a job. For a requested generation, use `kling_generate_video` for text or `kling_generate_video_from_image` for reference images. For reference-image animation, pass the user-selected source image to the image workflow. Choose the model and options listed by the installed package. Generation consumes credits. Review [current pricing](https://platform.acedata.cloud/models?utm_source=github&utm_medium=referral&utm_campaign=evergreen) before submitting, keep the task ID, and use `kling_get_task` to check that same task.

[Support](https://platform.acedata.cloud/support?utm_source=github&utm_medium=referral&utm_campaign=evergreen)
