# Google Search

![Google Search service artwork](assets/service-icon.png)

Search web, news, images, places, videos and maps through your Ace Data Cloud search application. This independent plugin connects Claude Code to the Google Search MCP hosted by Ace Data Cloud. [简体中文](readme/README_zh_Hans.md)

## Install

```text
/plugin marketplace add AceDataCloud/Skills
/plugin install google-search-by-ace-data-cloud@acedatacloud-skills
```

Sign in to [Applications](https://platform.acedata.cloud/console/applications?utm_source=github&utm_medium=referral&utm_campaign=evergreen) and open **General Application**. If it is missing, choose **Initialize General Application**. Click the copy button marked **1** next to **API KEY**. Check that your application has Google Search access.

![Copy button 1 beside the General Application API key](assets/get-api-key-en.png)

In Claude Code, open **/plugin → Installed → google-search-by-ace-data-cloud → Configure options** and enter the raw token into **Ace Data Cloud API Token**. The plugin sends it as a bearer token only to `https://serp.mcp.acedata.cloud/mcp`.

## Use the tools

Start with `serp_list_search_types`. It displays the available search types from local reference data. Pass the requested query and locale to `serp_google_search`. Read the output URLs directly.

Billed operations use your Ace Data Cloud balance. Consult [service pricing](https://platform.acedata.cloud/models?utm_source=github&utm_medium=referral&utm_campaign=evergreen) and the [service guide](https://platform.acedata.cloud/documents/serp-mcp?utm_source=github&utm_medium=referral&utm_campaign=evergreen).
