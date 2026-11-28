# Fish Audio by Ace Data Cloud

![Fish Audio 服务图](../assets/service-icon.png)

用自己的 Ace Data Cloud 应用将文本合成为语音，通过原任务 ID 获取音频。 [English](../README.md)

## 安装和配置

```text
/plugin marketplace add AceDataCloud/Skills
/plugin install fish-audio-by-ace-data-cloud@acedatacloud-skills
```

打开 [Ace Data Cloud 应用](https://platform.acedata.cloud/console/applications?utm_source=github&utm_medium=referral&utm_campaign=evergreen)，为通用应用创建有 Fish Audio 使用权限的专用令牌。[应用位置](../assets/get-api-key-en.png) · [创建密钥](../assets/create-api-key-en.png)。在 Claude Code 的 **/plugin → Installed → fish-audio-by-ace-data-cloud → Configure options** 中，将原始令牌填进 **Ace Data Cloud API Token**。插件会向 `https://fish.mcp.acedata.cloud/mcp` 发送 Bearer 凭据。

## 使用

先用 `fish_get_usage_guide` 读取本地语音使用说明，不执行语音合成。先读取语音用法，再按用户选择的文本和声音合成。已有任务可直接查询，避免重复提交。需要合成时使用 `fish_generate_audio`。若返回进行中的任务，使用同一 ID 调用 `fish_get_task` 取得音频地址或终态错误。

收费操作会使用 Ace Data Cloud 余额。[服务价格](https://platform.acedata.cloud/models?utm_source=github&utm_medium=referral&utm_campaign=evergreen) · [服务说明](https://platform.acedata.cloud/documents/fish?utm_source=github&utm_medium=referral&utm_campaign=evergreen)
