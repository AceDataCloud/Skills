# Seedream

![Seedream 服务图](../assets/service-icon.png)

用自己的 Ace Data Cloud 应用按提示词生成图像，或编辑用户选定的参考图。 [English](../README.md)

## 安装和配置

```text
/plugin marketplace add AceDataCloud/Skills
/plugin install seedream-by-ace-data-cloud@acedatacloud-skills
```

打开 [Ace Data Cloud 应用](https://platform.acedata.cloud/console/applications?utm_source=github&utm_medium=referral&utm_campaign=evergreen)，为通用应用创建有 Seedream 使用权限的专用令牌。[应用位置](../assets/get-api-key-en.png) · [创建密钥](../assets/create-api-key-en.png)。在 Claude Code 的 **/plugin → Installed → seedream-by-ace-data-cloud → Configure options** 中，将原始令牌填进 **Ace Data Cloud API Token**。插件会向 `https://seedream.mcp.acedata.cloud/mcp` 发送 Bearer 凭据。

## 使用

先用 `seedream_list_models` 读取本地模型清单，不消耗生成额度。按用户选择的模型、尺寸及参考图生成或编辑图像。查看工具的实时输入定义确认可用参数。新图使用 `seedream_generate_image`，编辑选定参考图使用 `seedream_edit_image`；查询进行中的任务时沿用原 ID 调用 `seedream_get_task`。

收费操作会使用 Ace Data Cloud 余额。[服务价格](https://platform.acedata.cloud/models?utm_source=github&utm_medium=referral&utm_campaign=evergreen) · [服务说明](https://platform.acedata.cloud/documents/seedream?utm_source=github&utm_medium=referral&utm_campaign=evergreen)
