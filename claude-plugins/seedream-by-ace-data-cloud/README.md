# Seedream

![Seedream service artwork](assets/service-icon.png)

Generate or edit Seedream images from a prompt and selected reference images through Ace Data Cloud. This independent plugin connects Claude Code to the Seedream MCP hosted by Ace Data Cloud. [简体中文](readme/README_zh_Hans.md)

## Install

```text
/plugin marketplace add AceDataCloud/Skills
/plugin install seedream-by-ace-data-cloud@acedatacloud-skills
```

Sign in to [Applications](https://platform.acedata.cloud/console/applications?utm_source=github&utm_medium=referral&utm_campaign=evergreen) and open **General Application**. If it is missing, choose **Initialize General Application**. Click the copy button marked **1** next to **API KEY**. Check that your application has Seedream access.

![Copy button 1 beside the General Application API key](assets/get-api-key-en.png)

In Claude Code, open **/plugin → Installed → seedream-by-ace-data-cloud → Configure options** and enter the raw token into **Ace Data Cloud API Token**. The plugin sends it as a bearer token only to `https://seedream.mcp.acedata.cloud/mcp`.

## Use the tools

Start with `seedream_list_models`. It shows the supported models from local reference data. Use `seedream_generate_image` for a new image and `seedream_edit_image` for an explicitly selected reference. Check a pending result with `seedream_get_task` using the original ID.

Billed operations use your Ace Data Cloud balance. Consult [service pricing](https://platform.acedata.cloud/models?utm_source=github&utm_medium=referral&utm_campaign=evergreen) and the [service guide](https://platform.acedata.cloud/documents/seedream?utm_source=github&utm_medium=referral&utm_campaign=evergreen).
