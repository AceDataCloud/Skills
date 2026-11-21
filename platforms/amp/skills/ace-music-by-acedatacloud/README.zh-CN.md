# 在 Amp 中使用 ACE Music

```sh
amp skill add AceDataCloud/Skills/platforms/amp/skills/ace-music-by-acedatacloud
```

也可以从已审核的源码目录运行 `amp skill add ./platforms/amp/skills/ace-music-by-acedatacloud`。在[应用管理](https://platform.acedata.cloud/console/applications?utm_source=amp&utm_medium=referral&utm_campaign=evergreen&utm_content=acemusic_amp_key)取得服务 Key，将其通过环境变量 `ACEDATACLOUD_API_TOKEN` 提供给 Amp 并加载此技能。使用 `amp mcp doctor acemusic-ace` 检查连接，使用 `acemusic_list_models` 免费查看模型。

输入主题或自定义标题、歌词、风格即可创作。该技能也支持上传参考音频、翻唱及双轨融合。使用收费工具前查看[当前价格](https://platform.acedata.cloud/services/acemusic?utm_source=amp&utm_medium=referral&utm_campaign=evergreen&utm_content=acemusic_amp_price)。保存原任务 ID 供后续查询。[English](README.md) · [使用流程](SKILL.md)
