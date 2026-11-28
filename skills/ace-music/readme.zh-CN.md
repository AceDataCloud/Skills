# ACE Music Agent Skill

```sh
npx skills add acedatacloud/skills --skill ace-music
```

选择正在使用的助手，安装后新开对话。

登录[应用列表](https://platform.acedata.cloud/console/applications)，打开**通用应用**。首次使用时先初始化通用应用，然后点击 **API KEY** 旁的复制按钮（图中标注 **1**）。把原始 Key 保存在运行助手的环境变量 `ACEDATACLOUD_API_TOKEN` 中。

![通用应用中的 API Key 复制按钮（标注 1）](https://raw.githubusercontent.com/AceDataCloud/NanoBananaDify/2522b2f57210597af2db866445319334a1677a23/_assets/tutorial/get-api-key-en.png)

若使用受限密钥，请允许 ACE Music 的歌曲、歌词和任务查询接口。

先问“ACE Music 能做什么？”即可阅读本地技能。创作时输入歌曲主题，或提供自己的标题、歌词和风格。还可以上传参考音频、翻唱一条自己的音轨或融合两条不同的音轨。创作歌词和导入参考音频分别计费。保存原任务 ID，可查询两首候选歌曲或恢复部分成功的音轨。[服务价格](https://platform.acedata.cloud/services/acemusic) · [接口示例](SKILL.md) · [English](README.md)
