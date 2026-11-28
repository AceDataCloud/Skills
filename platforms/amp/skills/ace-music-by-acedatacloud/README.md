# ACE Music for Amp

```sh
amp skill add AceDataCloud/Skills/platforms/amp/skills/ace-music-by-acedatacloud
```

From a reviewed checkout, use `amp skill add ./platforms/amp/skills/ace-music-by-acedatacloud`.

Sign in to [Applications](https://platform.acedata.cloud/console/applications?utm_source=amp&utm_medium=referral&utm_campaign=evergreen) and open **General Application**. Select **Initialize General Application** on first use, then click the copy icon to the right of **API KEY**.

![Get your Ace Data Cloud API key](https://cdn.acedata.cloud/dvc3cg.jpg)

Start Amp with the copied key in the `ACEDATACLOUD_API_TOKEN` environment variable and ask it to load this skill. Use `amp mcp doctor acemusic-ace` to check the connection and `acemusic_list_models` to inspect available models without creating a task.

Describe a song or supply a title, lyrics and style. The skill also supports uploading reference audio, covering one owned track or blending two. Inspect [current prices](https://platform.acedata.cloud/services/acemusic?utm_source=amp&utm_medium=referral&utm_campaign=evergreen) before using a billable tool. Preserve the original task ID for lookup. [Chinese](README.zh-CN.md) · [Workflow](SKILL.md)
