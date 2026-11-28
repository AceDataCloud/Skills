# Google Search

![Google Search 服务图](../assets/service-icon.png)

通过自己的 Ace Data Cloud 应用搜索网页、图片、新闻、视频、地点和地图，并返回来源链接。 [English](../README.md)

## 安装和配置

```text
/plugin marketplace add AceDataCloud/Skills
/plugin install google-search-by-ace-data-cloud@acedatacloud-skills
```

打开 [Ace Data Cloud 应用](https://platform.acedata.cloud/console/applications?utm_source=github&utm_medium=referral&utm_campaign=evergreen)，为通用应用创建有 Google Search 使用权限的专用令牌。[应用位置](../assets/get-api-key-en.png) · [创建密钥](../assets/create-api-key-en.png)。在 Claude Code 的 **/plugin → Installed → google-search-by-ace-data-cloud → Configure options** 中，将原始令牌填进 **Ace Data Cloud API Token**。插件会向 `https://serp.mcp.acedata.cloud/mcp` 发送 Bearer 凭据。

## 使用

先用 `serp_list_search_types` 读取本地搜索类型说明，不会运行网络搜索。按实际问题选择网页、图片或新闻等搜索类型，列出相关结果和链接。搜索查询可能消耗 Credits。使用 `serp_google_search` 执行用户要求的查询并读取来源链接。

收费操作会使用 Ace Data Cloud 余额。[服务价格](https://platform.acedata.cloud/models?utm_source=github&utm_medium=referral&utm_campaign=evergreen) · [服务说明](https://platform.acedata.cloud/documents/serp-mcp?utm_source=github&utm_medium=referral&utm_campaign=evergreen)
