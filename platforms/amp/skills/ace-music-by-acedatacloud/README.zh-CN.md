# 在 Amp 中使用 ACE Music

```sh
amp skill add AceDataCloud/Skills/platforms/amp/skills/ace-music-by-acedatacloud
```

也可以从已审核的源码目录运行 `amp skill add ./platforms/amp/skills/ace-music-by-acedatacloud`。

登录[应用列表](https://platform.acedata.cloud/console/applications?utm_source=amp&utm_medium=referral&utm_campaign=evergreen)，打开**通用应用**。首次使用时先初始化通用应用，然后点击 **API KEY** 旁的复制按钮（图中标注 **1**）。在启动 Amp 的终端把原始 Key 保存到 `ACEDATACLOUD_API_TOKEN`。

![通用应用中的 API Key 复制按钮（标注 1）](https://raw.githubusercontent.com/AceDataCloud/NanoBananaDify/2522b2f57210597af2db866445319334a1677a23/_assets/tutorial/get-api-key-en.png)

使用 `amp mcp doctor acemusic-ace` 检查连接，使用 `acemusic_list_models` 免费查看模型。

输入主题或自定义标题、歌词、风格即可创作。该技能也支持上传参考音频、翻唱及双轨融合。使用收费工具前查看[当前价格](https://platform.acedata.cloud/services/acemusic?utm_source=amp&utm_medium=referral&utm_campaign=evergreen)。保存原任务 ID 供后续查询。[English](README.md) · [使用流程](SKILL.md)
