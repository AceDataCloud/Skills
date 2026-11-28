# ACE Music Agent Skill

```sh
npx skills add acedatacloud/skills --skill ace-music
```

Select your agent and start a fresh session.

Sign in to [Applications](https://platform.acedata.cloud/console/applications) and open **General Application**. If it is missing, choose **Initialize General Application**. Click the copy button marked **1** next to **API KEY**. Store the raw key in the agent process’s `ACEDATACLOUD_API_TOKEN` environment variable.

![Copy button 1 beside the General Application API key](https://raw.githubusercontent.com/AceDataCloud/NanoBananaDify/2522b2f57210597af2db866445319334a1677a23/_assets/tutorial/get-api-key-en.png)

For a restricted key, allow the ACE Music audio, lyrics and task endpoints.

Ask “What can I do with ACE Music?” to read the installed instructions. For a song, use an idea or your own title, lyrics and style. The agent can upload a reference, cover an owned track or blend two different owned tracks. Generating lyrics and uploading a reference incur separate charges. Save the task ID and retrieve it to check the two candidates or recover a partial result. [Service price](https://platform.acedata.cloud/services/acemusic) · [API examples](SKILL.md) · [中文](readme.zh-CN.md)
