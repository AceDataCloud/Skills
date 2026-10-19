#!/usr/bin/env python3
"""Build independently installable ClawHub Skills from canonical service sources.

Preview is read-only; this tool deliberately has no upload option.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import urlencode

REPO = Path(__file__).resolve().parents[1]
CLI = ["npx", "--yes", "clawhub@0.23.3"]
SCREENSHOT = "https://raw.githubusercontent.com/AceDataCloud/SunoDify/8d3d03570e73324220f111f7fe343da0792a8071/_assets/tutorial/"
INSTALL_IMAGE = "suno-clawhub-20261017.jpg"


def link(service, placement, path="/console/applications"):
    return "https://platform.acedata.cloud" + path + "?" + urlencode({
        "utm_source": "agent_skill", "utm_medium": "referral",
        "utm_campaign": "evergreen", "utm_content": service["id"].replace("-", "_") + "_clawhub_" + placement})


def onboarding(service, zh=False):
    ref = "@acedatacloud/" + service["slug"]
    name = service["source"].split("/")[-1]
    routes = ", ".join("`" + r + "`" for r in service["routes"])
    config = json.dumps({"skills": {"entries": {name: {"enabled": True, "apiKey": "YOUR_ACE_SERVICE_API_KEY"}}}}, indent=2)
    if zh:
        return f'''# {service['display_name']}

这是 Ace Data Cloud 维护的 {service['id']} 集成，使用你自己的 Ace 服务 API Key；不声称是模型品牌方或 OpenClaw 官方发布。每个技能独立安装，不需要安装合集或额外 MCP。

## 1. 从官方目录安装

[ClawHub 条目](https://clawhub.ai/acedatacloud/skills/{service['slug']})（发布前可能尚不可用），确认发布者是 `@acedatacloud`：

```sh
openclaw skills install {ref}
```

旧版也可使用 `clawhub install {ref}`。本说明/预览不代表新版已通过审核；以真实条目和安装结果为准。

![真实 ClawHub Suno 安装入口，2026-10-17](assets/{INSTALL_IMAGE})

这是 Suno Skill 1.0.1 的真实历史目录页，仅说明发布者与安装入口；其他服务使用上面的各自条目。它不是本候选包的安装/运行结果，也不证明付费调用。图像来源与限制在包内 `assets/source.json`；新的原生 Key 配置实拍仍待补齐。

## 2. 注册并取得服务密钥

[注册或登录 Ace]({link(service,'signup','/')}) → [Applications]({link(service,'api_key')}) → **General application**（没有则先 Initialize General Application）。检查该服务的权限、余额和[当前价格]({link(service,'pricing','/models')})。
复制 API Key，或 **Manage Keys → Create** 创建专用密钥；按需限制有效期、额度和 Allowed APIs：{routes}。
只复制 Key 值，不加 `Bearer `。`platform-...` 管理 token 不能代替服务密钥。不要把 Key 发到聊天、截图或 Git。

![已有真实截图：复制密钥和 Manage Keys]({SCREENSHOT}get-api-key-en.png)
![已有真实截图：创建专用密钥]({SCREENSHOT}create-api-key-en.png)

配图来源：Ace SunoDify 固定提交的原始教程图，2026-10-18 复用；拍摄日期未声明，不代表当前账号实测。安装页面使用原生 ClawHub 入口；当前安装配置尚无新增界面截图。

## 3. 填入 OpenClaw 原生 Skill 配置

在运行 Gateway 的机器编辑 `~/.openclaw/openclaw.json`，把下面的 `skills.entries` 条目合并到现有配置，**不要覆盖整个文件**；把占位值替换为 Key：

```json
{config}
```

也可以只在 `~/.openclaw/.env` 设置 `ACEDATACLOUD_API_TOKEN=你的服务密钥`。选择一种方式，保护文件权限（例如 `chmod 600`），重启 Gateway 并开始新会话。
原生 `apiKey` 通过本技能的 `primaryEnv` 注入到宿主的当前 Agent 回合；沙箱不会自动继承，需按 [OpenClaw 官方配置](https://docs.openclaw.ai/tools/skills-config) 给沙箱单独注入同名环境变量。不要把真实 Key 粘贴到示例/提示词。

## 4. 首次使用与结果

确认本次成本并获得用户对生成的同意后，输入：**{service['query_zh']}**。具体请求字段、模型和例子在本包 `SKILL.md`，无需再安装别的服务。
预期：{service['expected_zh']}
返回任务 ID 后保存它，仅查询同一 ID，直到明确成功/失败；不要因超时或处理中重复提交付费生成。失败保留原始错误，不切换模型。用户内容/参考媒体会发送到 `api.acedata.cloud`，仅使用有权处理的内容。

## 常见问题

- 401：检查完整 Key、Gateway/沙箱环境，确保未把 `Bearer ` 作为 Key 的一部分。
- 403：核服务权限、Key 到期/额度/Allowed APIs；也可能是内容审核拒绝，按原错误处理。
- 429：降低频率；不要自动重试付费提交。
- 技能未出现：确认配置键为 `{name}`，重启并查看技能检查结果；需 `curl` 与服务 Key。
- Pending/5xx/超时：查询原 task，保留 trace ID，不能据预览 URL 宣称完成。

来源标记只用于注册前归因，不保证已经产生用户、收入或付费转化。
'''
    return f'''# {service['display_name']}

An Ace Data Cloud maintained integration for {service['id']}, using your own Ace service API key. This is not an official integration from the model brand or OpenClaw. Install this service alone; no suite or extra MCP is required.

## 1. Install from the native catalog

Open the [ClawHub listing](https://clawhub.ai/acedatacloud/skills/{service['slug']}) (it may be unavailable until publication) and verify publisher `@acedatacloud`:

```sh
openclaw skills install {ref}
```

Older/direct workflows can use `clawhub install {ref}`. Source/preview availability is not registry approval; inspect the real listing and installed version.

![Real ClawHub Suno install entry, 2026-10-17](assets/{INSTALL_IMAGE})

This historical Suno Skill 1.0.1 page shows the publisher and install entry only. Other services use their own listing above. It is not an installation or execution result for this candidate, and does not prove a paid call. See bundled `assets/source.json` for provenance and limits. A real screenshot of the new native Key configuration is still pending.

## 2. Register and copy a service key

[Register or sign in to Ace]({link(service,'signup','/')}) → [Applications]({link(service,'api_key')}) → **General application**. Choose **Initialize General Application** if needed. Check service access, balance and [current pricing]({link(service,'pricing','/models')}).
Copy its API Key or choose **Manage Keys → Create** for a dedicated key. Set expiry, usage limits and **Allowed APIs** as needed: {routes}.
Copy the raw value without `Bearer `. A `platform-...` account token is not a service key. Never put a real key in a prompt, screenshot or repository.

![Existing real screenshot: copy a key or open Manage Keys]({SCREENSHOT}get-api-key-en.png)
![Existing real screenshot: create a dedicated key]({SCREENSHOT}create-api-key-en.png)

Image source: original Ace SunoDify tutorial screenshots at the pinned commit, reused 2026-10-18; capture date is unspecified. They are key-location references, not a new account test. No new OpenClaw configuration screenshot is claimed.

## 3. Use OpenClaw's native Skill credential field

On the Gateway machine, merge this entry into `skills.entries` in `~/.openclaw/openclaw.json`; **do not replace the entire file**. Replace the placeholder privately:

```json
{config}
```

Alternatively set `ACEDATACLOUD_API_TOKEN=your_service_key` in `~/.openclaw/.env`. Choose one method, protect file permissions (for example `chmod 600`), restart the Gateway and start a new session.
The Skill's `primaryEnv` maps the native `apiKey` to the host agent turn. A sandbox does not automatically inherit it: configure the same variable separately for the sandbox per the [official Skills config](https://docs.openclaw.ai/tools/skills-config). Do not paste the key into a chat.

## 4. First use and result

After checking the cost and getting the user's agreement to generate, ask: **{service['query']}**
The exact request examples and model IDs are bundled in `SKILL.md`; no other service installation is required.
Expected result: {service['expected']}
Save any returned task ID and retrieve that same ID until explicit success or failure. A timeout or pending preview is not permission to submit again. Preserve errors rather than switching models. Prompts and referenced media are sent to `api.acedata.cloud`; use only content you are entitled to process.

## Troubleshooting

- 401: check the full key and Gateway/sandbox environment; do not include `Bearer ` inside the key value.
- 403: check access, expiry, limits and Allowed APIs; content moderation can also return 403, so read the error.
- 429: reduce rate; do not automatically retry a paid submission.
- Missing Skill: the configuration key is `{name}`; restart and check Skill eligibility. `curl` and the service key are required.
- Pending, 5xx or timeout: retrieve the original task, retain the trace ID and do not treat a preview URL as completion.

Acquisition tags identify pre-signup context only; they do not prove users, payments or revenue.
'''


def build(repo, service, output):
    source = repo / service["source"] / "SKILL.md"
    text = source.read_text()
    front, body = text.split("---", 2)[1:]
    name = re.search(r"^name: (.+)$", front, re.M).group(1)
    front = re.sub(r"^description:.*$", "description: " + service["description"], front, flags=re.M)
    runtime = {"requires": {"env": ["ACEDATACLOUD_API_TOKEN"], "bins": ["curl"]},
               "primaryEnv": "ACEDATACLOUD_API_TOKEN", "emoji": service["emoji"],
               "homepage": link(service, "api_key")}
    front = front.replace("metadata:\n", "metadata:\n  openclaw: " + json.dumps(runtime, ensure_ascii=False) + "\n")
    front = re.sub(r"^compatibility:.*$", "compatibility: Requires curl and an Ace service API key. OpenClaw native skills.entries apiKey is supported; sandbox credentials require separate configuration.", front, flags=re.M)
    # Preserve one canonical technical body; remove only duplicated onboarding prose.
    body = re.sub(r"\n## First-time setup\n.*?(?=\n## )", "\n", body, flags=re.S)
    body = re.sub(r"^> \*\*Setup:\*\*.*\n", "", body, flags=re.M)
    body = body.replace("../_shared/", "https://github.com/AceDataCloud/Skills/blob/main/skills/_shared/")
    body = body.replace("Continue until\n> `response.data[].video_url` appears or a terminal error is returned.", "Continue until explicit terminal success or failure. A video URL alone does not override a pending or failed task.")
    body = body.replace("# Happy Horse Video Generation and Editing", "# HappyHorse Video Generation and Editing")
    target = output / service["slug"]
    target.mkdir(parents=True, exist_ok=False)
    (target / "SKILL.md").write_text("---" + front + "---\n\n" + onboarding(service) + "\n## Service API reference\n" + body)
    (target / "README.md").write_text(onboarding(service))
    (target / "README.zh-CN.md").write_text(onboarding(service, zh=True))
    shutil.copytree(repo / "clawhub/assets", target / "assets")
    return {"service": service["id"], "source": service["source"], "bundle": str(target),
            "source_name": name, "slug": service["slug"], "display_name": service["display_name"],
            "categories": service["categories"], "topics": service["topics"],
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "bundle_files": {p.relative_to(target).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in sorted(target.rglob("*")) if p.is_file()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service", choices=["all", "suno", "seedance", "happyhorse", "gpt-image", "nano-banana"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preview", action="store_true", help="Run official read-only registry dry-runs; never upload")
    args = parser.parse_args()
    catalog = json.loads((REPO / "clawhub/catalog.json").read_text())
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    inputs = ["clawhub/catalog.json", "clawhub/assets", "scripts/build_clawhub_catalog.py"] + [s["source"] for s in catalog["services"]]
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all", "--", *inputs], cwd=REPO, text=True).strip()
    if args.preview and dirty:
        parser.error("Commit the reviewed catalog, builder and service inputs before attaching source provenance to a registry preview")
    services = [s for s in catalog["services"] if args.service in ("all", s["id"])]
    args.output.mkdir(parents=True, exist_ok=True)
    built = []
    for service in services:
        bundle = build(REPO, service, args.output)
        bundle["source_commit"] = commit
        command = CLI + ["--no-input", "skill", "publish", bundle["bundle"], "--owner", catalog["owner"],
                         "--slug", service["slug"], "--name", service["display_name"],
                         "--categories", ",".join(service["categories"]), "--topics", ",".join(service["topics"]),
                         "--source-repo", "AceDataCloud/Skills", "--source-commit", commit, "--source-ref", commit,
                         "--source-path", ".", "--changelog", "Native single-service onboarding and service-name discovery; built by scripts/build_clawhub_catalog.py.",
                         "--dry-run", "--json"]
        bundle["preview_command"] = command
        if args.preview:
            result = subprocess.run(command, text=True, capture_output=True)
            bundle["preview_exit_code"] = result.returncode
            bundle["preview"] = json.loads(result.stdout) if result.returncode == 0 else {"error": result.stderr}
        built.append(bundle)
    (args.output / "build.json").write_text(json.dumps({"source_commit": commit, "owner": catalog["owner"],
        "build_command": "python3 scripts/build_clawhub_catalog.py --service all --output <empty-directory>",
        "license_gate": "No upload. Human MIT-0 authorization and publisher access must be established before any release; source Apache-2.0 is preserved.",
        "services": built}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"bundles": len(built), "manifest": str(args.output / "build.json"), "upload": False}))
    if any(s.get("preview_exit_code", 0) != 0 for s in built):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
