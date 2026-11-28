# Kling

![Kling 服务图标](../assets/service-icon.png)

[English](../README.md) · 版本 0.1.0

用 Kling 将文字或参考图生成视频，并通过原任务 ID 查询结果。 本独立 Claude Code 插件由 Ace Data Cloud 维护。

## 安装和配置

先安装 [uv](https://docs.astral.sh/uv/)，确保 Claude Code 可运行 `uvx`。在客户端中输入：

```text
/plugin marketplace add AceDataCloud/Skills
/plugin install kling@acedatacloud-skills
```

在[应用管理](https://platform.acedata.cloud/console/applications?utm_source=github&utm_medium=referral&utm_campaign=evergreen)中[找到应用](../assets/get-api-key-en.png)，为 Kling [创建专用密钥](../assets/create-api-key-en.png)。把原始密钥填入本插件的 **Ace Data Cloud API Token** 掩码设置，不要贴到对话或项目文件。

## 使用

先用 `kling_list_models` 查看固定 MCP 包的本地模型说明。需要生成视频时，文字使用 `kling_generate_video`，参考图使用 `kling_generate_video_from_image`。参考图动画请使用用户选择的图片，并按包内模型说明选择受支持的参数。 生成会消耗积分，请先核对[当前价格](https://platform.acedata.cloud/models?utm_source=github&utm_medium=referral&utm_campaign=evergreen)，并保存返回的任务 ID。使用 `kling_get_task` 查询原任务。

[技术支持](https://platform.acedata.cloud/support?utm_source=github&utm_medium=referral&utm_campaign=evergreen)
