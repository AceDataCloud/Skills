# Seedance by Ace Data Cloud：skills.sh 首次使用

通过 Ace Data Cloud 的 API 在编程助手中使用 Seedance。本集成由 **Ace Data Cloud** 维护，不冒充 Seedance 原厂官方发布。每个技能可独立安装，不需要先安装通用账户技能或 MCP。

[English](README.md) · [skills.sh 安装入口](https://skills.sh/acedatacloud/skills/seedance-video) · [当前模型与价格](https://platform.acedata.cloud/models?utm_source=skills_sh&utm_medium=referral&utm_campaign=evergreen&utm_content=seedance_video_pricing)

## 1. 只安装这一个技能

确认仓库为 **acedatacloud/skills**，在项目终端运行：

```bash
npx --yes skills@1.7.2 add acedatacloud/skills --skill seedance-video -a codex --yes
npx --yes skills@1.7.2 list
```

`codex` 可换成已支持的 `claude-code` 或 `cursor`。Codex 文件位于 `.agents/skills/seedance-video/SKILL.md`；安装后开启新会话。安装不会生成媒体，也不会替你配置 Key。2026-10-18 验过的固定源码是 `v2026.1017.279001`；该版本先于这次说明改进，合并后默认分支才会包含新版说明。

![skills.sh真实安装控件](https://raw.githubusercontent.com/AceDataCloud/Skills/0901d63b7f7d216318463b1c33976838a084da3b/docs/skills-sh/installation-page-20261017.jpg)

这是 2026-10-17 拍摄的账户技能真实目录页，用于展示共同安装控件；请使用上面的本服务 slug，不把该图当本服务安装/生成结果。[图片来源和边界](https://github.com/AceDataCloud/Skills/blob/0901d63b7f7d216318463b1c33976838a084da3b/docs/skills-sh/image-sources.json)。

## 2. 注册、登录和复制 Token

打开 [Ace Data Cloud → 我的应用](https://platform.acedata.cloud/console/applications?utm_source=skills_sh&utm_medium=referral&utm_campaign=evergreen&utm_content=seedance_video_api_key)，先注册/登录。进入 **General application（通用应用）**；没有则初始化通用应用。核对 **Seedance** 的权限、余额和当前价。复制卡片上的 Key，或 **Manage Keys → Create** 创建单独 Key，例如 `skills.sh Seedance`。按需设置过期时间和用量限制；启用 Allowed APIs 时至少放行 `/seedance/videos`、`/seedance/tasks`，高级动作另查 SKILL.md。

![复制Key与管理密钥](https://raw.githubusercontent.com/AceDataCloud/SunoDify/8d3d03570e73324220f111f7fe343da0792a8071/_assets/tutorial/get-api-key-en.png)

![创建专用Key](https://raw.githubusercontent.com/AceDataCloud/SunoDify/8d3d03570e73324220f111f7fe343da0792a8071/_assets/tutorial/create-api-key-en.png)

两图来自既有 [SunoDify 教程的脱敏 Ace 控制台截图](https://github.com/AceDataCloud/SunoDify/blob/8d3d03570e73324220f111f7fe343da0792a8071/README.md)，2026-10-18 核验；不是 Seedance 在 skills.sh 跑通的截图。图中 `Dify tutorial` 只是名称示例，请改为自己的名称。只复制完整 Token 字符串，不加 `Bearer `、引号或遮挡字符；不能用 `platform-...` 平台管理 Token 代替服务 API Key。

## 3. Key 放在哪里

skills.sh 不保存凭据。若从终端启动编程助手，先在该终端导出 Key，再启动助手/新会话：

```bash
export ACEDATACLOUD_API_TOKEN="your_api_key_here"
```

已运行的 IDE 要从配置好的环境重启，或按它的官方说明设置私密环境变量；安装技能不代表自动加载 `.env`。不要把 Key 填进聊天、提交 Git 或输出日志。OpenClaw 的 Gateway 设置是另一路，不是本安装路径的前提。

## 4. 首次提交与结果

先读 [SKILL.md](SKILL.md) 的精确请求参数，要求助手用 **Seedance by Ace Data Cloud** 和 `doubao-seedance-2-0-260128` 准备一条请求，核当前费用后才确认向 `/seedance/videos` 提交。异步返回时保存 task ID，只向 `/seedance/tasks` 查询同一任务，直到成功/失败终态；不要重发生成来查看进度。结果字段按 SKILL.md 读取：Wait for the terminal `succeeded` result and use its returned video URL.

下面直接复用本技能 Quick Start 参数。**这是收费提交示例，只能在确认服务、当前价格与具体请求后执行；本教程未执行它：**

```bash
curl -X POST https://api.acedata.cloud/seedance/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "doubao-seedance-2-0-260128", "content": [{"type": "text", "text": "a dancer performing contemporary ballet in a misty forest"}], "async": true}'
```

若返回 task ID，用原 ID 替换 `YOUR_TASK_ID` 后只查询同一任务：

```bash
curl -X POST https://api.acedata.cloud/seedance/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id":"YOUR_TASK_ID"}'
```

同步 GPT Image 若已返回 `data[].url` 则无需查任务；异步或 pending 要继续同 ID 查询。最终应拿到真实返回的音频/视频/图片 URL；本页不伪造结果或账单。

本教程没有实际生成媒体。拿到媒体后，还需用原 task/request 对应记录核实唯一账单，不能把安装或示例当真实调用结果。

## 常见问题

- **401**：检查完整服务 Key、进程是否收到环境变量，Key 值里不要包含 Bearer。
- **403**：查服务权限、过期和 API 限制，也可能是内容审核，先读原错误。
- **400**：核对精确模型和参数，不自行替换模型。
- **429 / 超时 / pending / 5xx**：降并发，先查同一任务或请求历史，不自动重试收费提交。
- **媒体打不开**：确认终态，使用实际返回 URL；支持排障只提供 task/trace ID，不提供 Key。

联系 [dev@acedata.cloud](mailto:dev@acedata.cloud)。站点安装数不代表独立用户或营收；本页四项 UTM 只标识 skills.sh 来源，不证明注册或付费。
