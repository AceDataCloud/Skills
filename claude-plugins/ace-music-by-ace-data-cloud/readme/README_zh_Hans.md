# ACE Music

[English](../README.md)

在 Claude Code 中按描述或自定义歌词创作歌曲、上传参考音频、翻唱一首歌或融合两首歌。插件连接 [ACE Music MCP](https://platform.acedata.cloud/documents/mcp-acemusic)。

## 安装

```text
/plugin marketplace add AceDataCloud/Skills
/plugin install ace-music-by-ace-data-cloud@acedatacloud-skills
```

登录[应用列表](https://platform.acedata.cloud/console/applications?utm_source=github&utm_medium=referral&utm_campaign=evergreen)，打开**通用应用**。首次使用时先初始化通用应用，然后点击 **API KEY** 旁的复制按钮（图中标注 **1**）。确认应用可访问 ACE Music。 首次登录可先[注册账号](https://platform.acedata.cloud/?utm_source=github&utm_medium=referral&utm_campaign=evergreen)。

![通用应用中的 API Key 复制按钮（标注 1）](../assets/get-api-key-en.png)

将原始 Key 填入插件的敏感 API Token 设置。生成歌曲、导入参考音轨或创作歌词前，先查看余额和[当前价格](https://platform.acedata.cloud/services/acemusic?utm_source=github&utm_medium=referral&utm_campaign=evergreen)。

需要独立的受限密钥时，可以选择 **Manage Keys → Create**。

![创建专用 Key](../assets/create-api-key-en.png)

## 第一次使用

先问“ACE Music 支持哪些模型和操作？”助手可以调用 `acemusic_list_models` 和 `acemusic_get_capabilities` 查看，无需创建任务。创作时可以给出主题，也可以直接提供标题、歌词和风格。歌曲生成支持默认的 `acemusic-v1.1` 和 `acemusic-v1`，成功后交付两首 MP3 候选。

翻唱使用一条自己名下的平台音轨 ID，融合需要两条不同的兼容音轨 ID，均使用 `acemusic-v1.1` 并提供歌词和风格。导入 HTTPS MP3 和生成歌词分别计费。提交后保存任务 ID，用同一 ID 免费查询。遇到 `partial_failed` 时返回已完成的音轨并说明部分失败，`submission_unknown` 时保留原任务以便核对。
