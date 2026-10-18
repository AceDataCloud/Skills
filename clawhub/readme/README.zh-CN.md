# ClawHub 单服务技能

用户应能直接搜索 **Suno、Seedance、HappyHorse、GPT Image、Nano Banana**，只安装需要的技能，再使用自己的 Ace 服务 API Key。标题拟为“服务名 by Ace Data Cloud”，说明 Ace 是维护者，不冒充模型品牌方或 OpenClaw 官方。

单一技术源码仍在 `skills/`，`clawhub/catalog.json` 维护五项真实服务映射。构建器把对应技术参考与首用模板组合为五个独立安装包，不复制实现仓、不修改 skills.sh 的源技能，也不要求安装通用合集或额外 MCP。

```sh
python3 scripts/build_clawhub_catalog.py --service all --output /tmp/ace-clawhub-review
python3 scripts/build_clawhub_catalog.py --service all --output /tmp/ace-clawhub-preview --preview
```

每次使用空输出目录。构建器**没有上传选项**；`--preview` 仅走官方干跑。`build.json` 保存源码 commit、输入/输出 hash、构建命令与每个条目的预览命令。

每个包内有英文/中文 README 及自包含 `SKILL.md`：官方目录安装→注册登录→Applications/General application→复制或创建专用 Key、核权限/余额/当前价格→OpenClaw 原生 `skills.entries.<skill-name>.apiKey` 字段→首次使用→同一 task 查询→成功/失败与常见问题。Key 图片复用固定来源的真实教程图，注明 2026-10-18 复用、拍摄日期未声明；没有伪造配置截图。

原生 runtime metadata 声明 `curl`、Key 环境变量及 `primaryEnv`，方便宿主识别凭据；沙箱不自动继承 Key，按官方文档单独配置。使用服务专用 emoji，不冒用品牌官方图标。已有目录 icon 为空，不声称已补图标。

2026-10-18：Suno、Seedance、Nano Banana 已有 **Skill** 1.0.1；新标题/元数据/引导只是待审包。HappyHorse、GPT Image 尚未核实公开的**文本 Skill**，需先在现有 publisher 后台核 hidden/pending，避免重复。

另有五个**代码插件**已经公开：`@acedatacloud/<service>-openclaw`，Suno 0.1.2、其余四项 0.1.1，由 [OpenClawProvider 原负责人](https://github.com/AceDataCloud/OpenClawProvider/pull/18)维护。[HappyHorse](https://clawhub.ai/acedatacloud/plugins/happyhorse-openclaw) 与 [GPT Image](https://clawhub.ai/acedatacloud/plugins/gpt-image-openclaw)已有这条安装路径，不能把“缺文本 Skill”说成“ClawHub 没有这两个服务”。本目录仅负责不同的文本 Skill 分发。

五个候选包随包提供字节不变的真实 ClawHub Suno 安装页原图与 `assets/source.json`：截图日期为 2026-10-17、Skill 1.0.1，只说明目录入口，不证明新候选安装或付费生成。中文预期结果使用中文；原生 Key 配置界面仍待真实截图，不绘制替代。

Backend 当前认可 `agent_skill/referral`，未定义 `clawhub` source，因此使用四项 UTM：`agent_skill / referral / evergreen / <service>_clawhub_<placement>`。不修改全局归因合同，不承诺已有注册或收入。

正式上传会接受 ClawHub MIT-0 条款，不能把源码 Apache-2.0 当组织授权。必须先有明确许可和现有组织发布权限；本构建器不上传、不接受协议。公开搜索、安装、真实执行、终态音视频和唯一账单需逐段验收。

详细映射和官方政策链接见[英文说明](README.md)。OpenClaw 原生 LLM Provider 与单服务代码插件由 OpenClaw 专属负责人推进，本目录只负责 ClawHub 的独立 Skills。
