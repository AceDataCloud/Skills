# ACE Music

[简体中文](readme/README_zh_Hans.md)

Create songs from a description or custom lyrics, upload a reference, cover one track, or blend two tracks. The plugin connects Claude Code to the [ACE Music MCP server](https://platform.acedata.cloud/documents/mcp-acemusic).

## Install in Claude Code

```text
/plugin marketplace add AceDataCloud/Skills
/plugin install ace-music-by-ace-data-cloud@acedatacloud-skills
```

Sign in to [Applications](https://platform.acedata.cloud/console/applications?utm_source=github&utm_medium=referral&utm_campaign=evergreen) and open **General Application**. If it is missing, choose **Initialize General Application**. Click the copy button marked **1** next to **API KEY**. Confirm the application can access ACE Music. New users can [register here](https://platform.acedata.cloud/?utm_source=github&utm_medium=referral&utm_campaign=evergreen).

![Copy button 1 beside the General Application API key](assets/get-api-key-en.png)

Paste the raw key into the plugin's sensitive API Token setting. Check your allowance and [current prices](https://platform.acedata.cloud/services/acemusic?utm_source=github&utm_medium=referral&utm_campaign=evergreen) before submitting a song, an upload or a lyrics request.

For a separate restricted key, choose **Manage Keys → Create**.

![Create a dedicated service key](assets/create-api-key-en.png)

## First request

Ask “Which ACE Music models and operations can I use?” The assistant can call `acemusic_list_models` and `acemusic_get_capabilities` without creating a task. To make a song, describe it or supply a title, lyrics and style. Song generation supports `acemusic-v1.1` (default) and `acemusic-v1`. A successful song task returns two MP3 candidates.

To cover a track or blend two tracks, supply your own platform audio IDs, lyrics and style. Both use `acemusic-v1.1`. Importing an HTTPS MP3 is a separate paid action, as is generating lyrics. For task recovery, use the original task ID. On `partial_failed`, return the available track and report the partial result. On `submission_unknown`, retain the ID for reconciliation. Authenticated task lookup is free.
