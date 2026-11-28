# Fish Audio

![Fish Audio service artwork](assets/service-icon.png)

Convert text to speech with a selected voice and retrieve existing audio task results through Ace Data Cloud. This independent plugin connects Claude Code to the Fish Audio MCP hosted by Ace Data Cloud. [简体中文](readme/README_zh_Hans.md)

## Install

```text
/plugin marketplace add AceDataCloud/Skills
/plugin install fish-audio-by-ace-data-cloud@acedatacloud-skills
```

Sign in to [Applications](https://platform.acedata.cloud/console/applications?utm_source=github&utm_medium=referral&utm_campaign=evergreen) and open **General Application**. If it is missing, choose **Initialize General Application**. Click the copy button marked **1** next to **API KEY**. Check that your application has Fish Audio access.

![Copy button 1 beside the General Application API key](assets/get-api-key-en.png)

In Claude Code, open **/plugin → Installed → fish-audio-by-ace-data-cloud → Configure options** and enter the raw token into **Ace Data Cloud API Token**. The plugin sends it as a bearer token only to `https://fish.mcp.acedata.cloud/mcp`.

## Use the tools

Start with `fish_get_usage_guide`. It returns local usage information without synthesizing audio. Use `fish_generate_audio` for requested speech. If it returns a pending task ID, use `fish_get_task` with that ID until the service returns an audio URL or a terminal failure.

Billed operations use your Ace Data Cloud balance. Consult [service pricing](https://platform.acedata.cloud/models?utm_source=github&utm_medium=referral&utm_campaign=evergreen) and the [service guide](https://platform.acedata.cloud/documents/fish?utm_source=github&utm_medium=referral&utm_campaign=evergreen).
