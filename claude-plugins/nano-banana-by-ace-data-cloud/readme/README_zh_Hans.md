# Nano Banana by Ace Data Cloud

[English](../README.md) · 版本 0.1.0

这是 Ace Data Cloud 提供的 **Nano Banana image服务独立插件**，不是 Nano Banana 模型厂商或 Anthropic 官方插件。仅复用现有 MCP，不改变 Claude 的聊天模型；付费请求按 Ace Credits 计费。

## 1. 安装入口

五个独立插件已于 2026-10-19 随源码 `605e92ed` 进入公开 Ace Git marketplace。在 Claude Code 中执行：

```text
/plugin marketplace add AceDataCloud/Skills
/plugin install nano-banana-by-ace-data-cloud@acedatacloud-skills
```

在已添加市场的 `/plugin` → Discover 搜 **Nano Banana** 或 **nano-banana-by-ace-data-cloud**。这是 **Ace 自有 marketplace 的原生插件安装**，不是 Anthropic 官方目录已收录。公开 main 已包含五个 0.1.0 插件；2026-10-19 已用官方 Claude Code 2.1.303 从公开 GitHub 正常添加市场并逐项独立安装，查看五项原生敏感 Token 配置。它证明自有市场公开安装，不证明 Anthropic 官方目录收录或真实付费业务成功。旧媒体合集仍可选，不需要安装全套；避免同时启用重复服务。

初始安装验证使用 2.1.81；2026-10-19 已使用官方 Release 且 SHA256 校验的 Claude Code 2.1.303 通过严格manifest、五项安装、原生敏感配置/脱敏读取和仅本机的 header/env 替换测试。它不替代普通公开安装、真实账号认证或付费首调。

## 2. 登录 Ace 并获取专用 Token

1. [注册或登录 Ace Data Cloud](https://platform.acedata.cloud/?utm_source=github&utm_medium=referral&utm_campaign=evergreen&utm_content=nano_banana_claude_signup)，打开 [Applications 应用列表](https://platform.acedata.cloud/console/applications?utm_source=github&utm_medium=referral&utm_campaign=evergreen&utm_content=nano_banana_claude_api_key)，选择 **General application 通用应用**；没有时先初始化。
2. 检查 **Nano Banana** 权限、余额和 [当前价格](https://platform.acedata.cloud/documents/nano-banana?utm_source=github&utm_medium=referral&utm_campaign=evergreen&utm_content=nano_banana_claude_pricing)。在应用卡片复制 Key，或 **Manage Keys / 管理密钥 → Create / 创建**，给本插件建单独 Key，名称建议 `Nano Banana Claude Code`。
3. 按需设置有效期、使用额度和 **Allowed APIs**，本流程需要 `/nano-banana/images`, `/nano-banana/tasks`。只开放需要的接口。

![通用应用复制 Key 与管理密钥入口，真实信息已遮盖](../assets/get-api-key-en.png)

![创建密钥的真实原图，图中旧示例名为 Dify tutorial](../assets/create-api-key-en.png)

两图来自 [SunoDify 固定版本](https://github.com/AceDataCloud/SunoDify/tree/8d3d03570e73324220f111f7fe343da0792a8071/_assets/tutorial)，2026-10-18 下载并目视核对，拍摄日期未知。旧图中的 **Dify tutorial** 只是原例子，请为此插件填写 **Nano Banana Claude Code**。复制 Token 本身，不加 `Bearer `、空格或引号；`platform-...` 管理 Token、Anthropic 或模型厂商的 Key 都不能代替 Ace 服务 Key。

## 3. 在插件原生配置中粘贴

启用插件，在 `/plugin` → **Installed** → **nano-banana-by-ace-data-cloud** → **Configure options** 的 **Ace Data Cloud API Token** 中粘贴。插件声明了 `sensitive: true`；按当前官方文档，该值与 settings.json 分开保存并填入 MCP 配置。macOS 优先 Keychain，写入失败会退回 .credentials.json；无受支持 keychain 的平台也使用该凭据文件。实际使用前核对本机存储路径与文件保护，不能承诺所有平台都进 Keychain。不要把 Key 放进聊天、Git、截图或共享配置。这里使用固定 Ace Token，不同时给相同连接配置 OAuth；插件不会自动充值或扩大权限。

2.1.303 起可用 `claude plugin configure nano-banana-by-ace-data-cloud@acedatacloud-skills --json` 只查看已配置状态，不回显敏感值；`--values-stdin` 是原生本地输入接口，应接可信秘密来源，真实 Token 不放命令参数、提示词或共享文件。配置保存成功不代表服务已经接受凭据。

![历史真实 Claude 自定义连接弹窗，示例是 Suno](../assets/claude-custom-connector-historical.png)

这是未改动的历史 **Web/Desktop 自定义连接器** 图，2026-10-17 下载核验，拍摄日/版本未知；Suno 的 Add 尚未点击。它不是本插件 `/plugin` Token 配置界面，也不证明授权、上架或执行。实际 Token 对话框由协调队列实拍，未造假界面。

## 4. 免费检查、首用与同 ID 查询

免费验证：先请 Claude 解释本插件操作，不调用远端工具。该服务暂无本地模型列表工具，不要为测试安装发起图片生成。

付费首用前明确模型、输入、张数/时长和当前价格，执行须以你对该次请求的授权为准。返回任务 ID 后只查询 **同一 ID** 直到成功/失败，不重新发生成；返回最终成功和媒体 URL 后再显示结果。仅有 Connected、工具列表、任务 ID 或部分预览不代表完成。查询旧任务也不能授权新生成。

工具名：`nanobanana_generate_image`, `nanobanana_edit_image`, `nanobanana_get_task`。



## 常见问题与隐私

- 找不到插件：先添加 Ace 市场，或执行 `claude plugin marketplace update acedatacloud-skills` 后核对服务 slug；组织允许列表或 Git 下载失败也可能阻止安装。Anthropic 官方目录仍未确认。
- 401：核对原始 Token、有效期、应用/服务/API 权限；不要填写其他厂商密钥。
- 余额不足、403、429：查看原错误，检查权限/内容限制/余额，遵守限速，不自动重发付费请求。
- 任务 pending：按服务说明轮询原 ID，不用“再生成一次”查进度。
- 官方目录：[政策 §4.B](https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy)限制独立 AI 图/音/视频生成，除非获得书面允许；本插件不冒称获准，不绕过准入。

插件没有 hooks、遥测、后台生成或自动装软件；MCP 只接收配置的 Ace 凭据和所选工具参数。只发送用户选定的提示词/参考媒体，不发送无关会话和文件。服务端存储见 [隐私政策](https://platform.acedata.cloud/privacy)、[条款](https://platform.acedata.cloud/terms) 与 [支持](https://platform.acedata.cloud/support)。集成图标使用 Ace 标志，准确标识提供方。

[完整英文步骤与三个示例](../README.md) · [已有维护源](https://github.com/AceDataCloud/Skills/tree/main/skills/nano-banana-image)
