# 在 Amp 中使用 ACE Music

```sh
amp skill add AceDataCloud/Skills/platforms/amp/skills/ace-music-by-acedatacloud
```

也可以从已审核的源码目录运行 `amp skill add ./platforms/amp/skills/ace-music-by-acedatacloud`。

登录[应用列表](https://platform.acedata.cloud/console/applications?utm_source=amp&utm_medium=referral&utm_campaign=evergreen)，打开**通用应用**。首次使用时先初始化通用应用，再点击 **API KEY** 一栏右侧的复制按钮。

![获取 Ace Data Cloud API Key](https://cdn.acedata.cloud/dvc3cg.jpg)

将复制的原始 Key 保存到环境变量 `ACEDATACLOUD_API_TOKEN` 后启动 Amp 并加载此技能。使用 `amp mcp doctor acemusic-ace` 检查连接，使用 `acemusic_list_models` 免费查看模型。

输入主题或自定义标题、歌词、风格即可创作。该技能也支持上传参考音频、翻唱及双轨融合。使用收费工具前查看[当前价格](https://platform.acedata.cloud/services/acemusic?utm_source=amp&utm_medium=referral&utm_campaign=evergreen)。保存原任务 ID 供后续查询。[English](README.md) · [使用流程](SKILL.md)
