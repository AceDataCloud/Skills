# ACE Music Agent Skill

```sh
npx skills add acedatacloud/skills --skill ace-music
```

Select your agent and start a fresh session.

Sign in to [Applications](https://platform.acedata.cloud/console/applications) and open **General Application**. Click the copy icon to the right of **API KEY**.

![Get your Ace Data Cloud API key](https://cdn.acedata.cloud/dvc3cg.jpg)

Give the agent process the copied key in `ACEDATACLOUD_API_TOKEN`. If you restrict the key, allow the ACE Music audio, lyrics and task APIs.

Ask “What can I do with ACE Music?” to read the installed instructions. For a song, use an idea or your own title, lyrics and style. The agent can upload a reference, cover an owned track or blend two different owned tracks. Generating lyrics and uploading a reference incur separate charges. Save the task ID and retrieve it to check the two candidates or recover a partial result. [Service price](https://platform.acedata.cloud/services/acemusic) · [API examples](SKILL.md) · [中文](readme.zh-CN.md)
