# ACE Music Agent Skill

```sh
npx skills add acedatacloud/skills --skill ace-music
```

选择正在使用的助手，安装后新开对话。

登录[应用列表](https://platform.acedata.cloud/console/applications)，打开**通用应用**。首次使用时先初始化通用应用，再点击 **API KEY** 一栏右侧的复制按钮。

![获取 Ace Data Cloud API Key](https://cdn.acedata.cloud/dvc3cg.jpg)

将原始 Key 通过环境变量 `ACEDATACLOUD_API_TOKEN` 提供给助手进程。如果使用受限密钥，请确认可访问 ACE Music 歌曲、歌词和任务 API。

先问“ACE Music 能做什么？”即可阅读本地技能。创作时输入歌曲主题，或提供自己的标题、歌词和风格。还可以上传参考音频、翻唱一条自己的音轨或融合两条不同的音轨。创作歌词和导入参考音频分别计费。保存原任务 ID，可查询两首候选歌曲或恢复部分成功的音轨。[服务价格](https://platform.acedata.cloud/services/acemusic) · [接口示例](SKILL.md) · [English](README.md)
