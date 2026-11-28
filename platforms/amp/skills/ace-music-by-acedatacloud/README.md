# ACE Music for Amp

```sh
amp skill add AceDataCloud/Skills/platforms/amp/skills/ace-music-by-acedatacloud
```

From a reviewed checkout, use `amp skill add ./platforms/amp/skills/ace-music-by-acedatacloud`.

Sign in to [Applications](https://platform.acedata.cloud/console/applications?utm_source=amp&utm_medium=referral&utm_campaign=evergreen) and open **General Application**. If it is missing, choose **Initialize General Application**. Click the copy button marked **1** next to **API KEY**. Save the raw key in `ACEDATACLOUD_API_TOKEN` in the environment that starts Amp.

![Copy button 1 beside the General Application API key](https://raw.githubusercontent.com/AceDataCloud/NanoBananaDify/2522b2f57210597af2db866445319334a1677a23/_assets/tutorial/get-api-key-en.png)

Use `amp mcp doctor acemusic-ace` to check the connection and `acemusic_list_models` to inspect available models without creating a task.

Describe a song or supply a title, lyrics and style. The skill also supports uploading reference audio, covering one owned track or blending two. Inspect [current prices](https://platform.acedata.cloud/services/acemusic?utm_source=amp&utm_medium=referral&utm_campaign=evergreen) before using a billable tool. Preserve the original task ID for lookup. [Chinese](README.zh-CN.md) · [Workflow](SKILL.md)
