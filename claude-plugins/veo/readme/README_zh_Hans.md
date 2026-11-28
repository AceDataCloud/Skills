# Veo

![Veo 服务图标](../assets/service-icon.png)

[English](../README.md) · 版本 0.1.0

用 Veo 根据文字或参考帧生成视频，再从原任务查询最终结果。 本独立 Claude Code 插件由 Ace Data Cloud 维护。

## 安装和配置

先安装 [uv](https://docs.astral.sh/uv/)，确保 Claude Code 可运行 `uvx`。在客户端中输入：

```text
/plugin marketplace add AceDataCloud/Skills
/plugin install veo@acedatacloud-skills
```

在[应用管理](https://platform.acedata.cloud/console/applications?utm_source=github&utm_medium=referral&utm_campaign=evergreen)中[找到应用](../assets/get-api-key-en.png)，为 Veo [创建专用密钥](../assets/create-api-key-en.png)。把原始密钥填入本插件的 **Ace Data Cloud API Token** 掩码设置，不要贴到对话或项目文件。

## 使用

先用 `veo_list_models` 查看固定 MCP 包的本地模型说明。需要生成视频时，文字使用 `veo_text_to_video`，参考图使用 `veo_image_to_video`。参考帧的数量和顺序取决于模型，可查看包内提示词指南。 生成会消耗积分，请先核对[当前价格](https://platform.acedata.cloud/models?utm_source=github&utm_medium=referral&utm_campaign=evergreen)，并保存返回的任务 ID。使用 `veo_get_task` 查询原任务。

[技术支持](https://platform.acedata.cloud/support?utm_source=github&utm_medium=referral&utm_campaign=evergreen)
