# Maestro 视频生成 API 对接说明

Maestro 是一个 **Agent 原生**的视频生产接口：你用一句自然语言 `prompt` 描述想要的视频（可选地用 `file_urls` 附上参考图片 / 视频 / 音频），一个无头的「AI 导演」会自动完成选题、写脚本、生成画面、配音、配乐、合成与渲染，最终产出带字幕的成片并上传 CDN。

本文将详细介绍 Maestro 视频生成 API 的对接说明，帮助您快速集成并充分利用该 API 的能力。

这是一个**异步任务**接口：提交后会立即返回 `task_id`，随后通过 [Maestro 任务查询 API](development_maestro_tasks.md)（`POST /maestro/tasks`）轮询获取结果（轮询免费不计费）。要在已有视频上继续迭代，可使用 `action: remix` / `edit` / `extend` 配合 `ref_task_id`。

## 申请流程

要使用 Maestro 视频生成 API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Maestro 视频生成 API →](https://platform.acedata.cloud/documents/maestro-videos)

## 基本使用

`POST https://api.acedata.cloud/maestro/videos`

最基础的用法只需要传入一个自然语言 `prompt`，AI 导演会自动决定脚本、画面、配音与剪辑。这里我们先了解下需要设置的请求头与请求体。

**Request Headers** 包括：

- `accept`：想要接收怎样格式的响应结果，这里填写为 `application/json`，即 JSON 格式。
- `authorization`：调用 API 的密钥，申请之后可以直接下拉选择。
- `content-type`：请求体的格式，这里填写为 `application/json`。

**Request Body** 主要包括：

- `prompt`：用自然语言描述要做的视频（主题、要展示什么、风格、受众）。
- `langs`：输出语言数组，如 `["zh-cn", "en"]`，默认 `["zh-cn"]`。
- `aspect`：画面比例，`9:16`（默认）/ `16:9` / `1:1`。
- `duration`：目标时长（秒），默认 30。

请求体的全部字段如下表所示：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `prompt` | string | 是 | 用自然语言描述要做的视频（主题、要展示什么、风格、受众）。脚本、画面、配音、剪辑都由 AI 决定 |
| `action` | string | 否 | `generate`（默认，生成新视频）/ `remix` / `edit` / `extend`（在已有视频上迭代，需配合 `ref_task_id`） |
| `ref_task_id` | string | 否 | 当 `action` 为 remix / edit / extend 时必填：作为起点的历史任务 `task_id` |
| `file_urls` | string[] | 否 | 参考媒体（图片 / 视频 / 音频 URL），例如要出镜的产品图、logo，或要加字幕的素材片段 |
| `langs` | string[] | 否 | 输出语言，如 `["zh-cn", "en"]`，默认 `["zh-cn"]`。第一个为主语言；每多一种语言复用画面、只多配音 + 渲染，**每多一种 +6 积分** |
| `aspect` | string | 否 | `9:16`（默认）/ `16:9` / `1:1`，统一输出 1080p/30fps |
| `duration` | int | 否 | 目标时长（秒），默认 30，支持 **5–300 秒**。按实际成片时长计费，但不会超过请求时长 |
| `scenario` | string | 否 | 视频类型：`auto` / `narrated` / `captions` / `avatar` / `drama`。`captions` 需传源视频，`avatar` 需传人像 |
| `style` | string | 否 | 视觉风格预设：`auto`（默认）/ `cinematic` / `glass` / `luxury` / `swiss` / `modern` / `editorial` / `warm` / `vibrant` / `neon` / `mono` / `pastel` / `bold` / `industrial` / `futuristic` / `retro`，也接受自由文本作为软提示。与 `scenario` 正交、不改变路由 |
| `voice` | string | 否 | 旁白音色（与语言无关，跨语言通用）：`auto`（默认）/ `warm-female` / `bright-female` / `anchor-female` / `clean-female` / `calm-male` / `deep-male` / `documentary-male` / `energetic-male` / `storyteller-male` |

下面通过一个具体示例来演示。假设我们要生成一条中英双语、竖屏、20 秒的科普短视频，对应的 CURL 代码如下：

```bash
curl -X POST 'https://api.acedata.cloud/maestro/videos' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "prompt": "用 20 秒讲清楚什么是向量数据库，适合零基础观众，结尾给一句记忆点",
  "langs": ["zh-cn", "en"],
  "aspect": "9:16",
  "duration": 20
}'
```

对应的 Python 代码如下：

```python
import requests

url = "https://api.acedata.cloud/maestro/videos"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "prompt": "用 20 秒讲清楚什么是向量数据库，适合零基础观众，结尾给一句记忆点",
    "langs": ["zh-cn", "en"],
    "aspect": "9:16",
    "duration": 20
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

点击运行，可以发现会立即得到一个结果，如下：

```json
{
  "success": true,
  "task_id": "f57e99c4f60f4373a15517742ce2357d",
  "trace_id": "70e1cb12-c619-4292-a416-90191205996b"
}
```

返回结果的字段介绍如下：

- `success`：此次任务是否成功提交。
- `task_id`：此次视频生成任务的 ID，后续用它去 [Maestro 任务查询 API](development_maestro_tasks.md) 轮询结果。
- `trace_id`：本次请求的追踪 ID，遇到问题时可提供给技术支持定位。

由于视频生产耗时较长，接口在此**立即返回 `task_id`**，并不会等到视频渲染完成。接下来需要用 `task_id` 去轮询结果，详见「取结果」一节。

## 指定视频类型与风格（scenario / style）

不传 `scenario` 时由 AI 自动判断（等于 `auto`）；想把视频钉到某种类型就显式传。例如做一条**竖屏短剧**，可以指定如下内容：

- `scenario`：视频类型，这里设为 `drama`（角色 + 对白的短剧）。
- `style`：视觉风格，这里设为 `cinematic`（电影质感）。

填写样例的 CURL 代码如下：

```bash
curl -X POST 'https://api.acedata.cloud/maestro/videos' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "prompt": "两个合租室友因为一只猫闹翻又和好，三幕反转，结尾温暖",
  "scenario": "drama",
  "style": "cinematic",
  "aspect": "9:16",
  "duration": 40
}'
```

常见的搭配方式：

- 解说短片：`scenario: "narrated"`，Lite / Standard / Pro 均支持。
- 自动字幕：`scenario: "captions"`，需用 `file_urls` 传源视频，Lite / Standard / Pro 均支持。
- 数字人 / 口播：`scenario: "avatar"`，需用 `file_urls` 传一张人像，Standard / Pro 支持。
- 短剧：`scenario: "drama"`（角色 + 对白），仅 Pro 支持。
- `style` 是视觉风格预设（如 `modern` / `neon` / `luxury`），不改变类型、只影响观感。
- `voice` 用来指定旁白音色（如 `warm-female` / `deep-male`），与语言无关、跨语言通用。

返回结果与「基本使用」一致，同样是立即返回 `task_id`。

## 多语言输出

在 `langs` 中传入多个语言即可一次产出多语言版本。第一个为主语言，之后每多一种语言会**复用同一套画面**，只额外配音 + 渲染，因此**每多一种语言仅 +6 积分**。示例：

```bash
curl -X POST 'https://api.acedata.cloud/maestro/videos' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "prompt": "介绍我们的智能客服产品，突出 3 个核心卖点",
  "langs": ["zh-cn", "en", "ja"],
  "aspect": "16:9",
  "duration": 30
}'
```

任务完成后，每种语言会对应结果里的一个 `variant`（见 [Maestro 任务查询 API](development_maestro_tasks.md)）。

## 在已有视频上迭代（remix / edit / extend）

传入 `action` 与上一次任务的 `ref_task_id`，即可在原项目基础上做差量修改（如「把第 2 幕标题改掉」「换个配音」「整体调暗」）。小改动很快、大改动会重做：

```bash
curl -X POST 'https://api.acedata.cloud/maestro/videos' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "action": "remix",
  "ref_task_id": "f57e99c4f60f4373a15517742ce2357d",
  "prompt": "把开场标题换成更有冲击力的一句，整体配色更暗一些"
}'
```

- `remix`：在原视频结构上重新演绎（保留主题，调整表现）。
- `edit`：对指定局部做精修（如换标题、换配音、调色）。
- `extend`：在原视频基础上延展内容。

返回结果同样是立即返回一个新的 `task_id`，用它轮询即可拿到迭代后的成片。

## 取结果

由于视频生产耗时较长，本接口在提交后立即返回 `task_id`，你需要用它去 [Maestro 任务查询 API](development_maestro_tasks.md) 轮询结果：

```bash
curl -X POST 'https://api.acedata.cloud/maestro/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "id": "f57e99c4f60f4373a15517742ce2357d"
}'
```

任务完成时会返回成片信息（每种语言对应一个 `variant`）。`status` 会经历 `pending → planning → producing → succeeded`（或 `failed`），**轮询免费、不消耗积分**。完整的响应格式与历史列表查询请参考 [Maestro 任务查询 API 对接说明](development_maestro_tasks.md)。

## 计费

**任务完成后按实际成片计费，失败的任务不扣费。** 计费以实际交付的成片时长与语言数为准，且计费时长不会超过请求时长。某个语言最终没有产出时，也不会收取该语言的 +6 加价。提交任务本身不单独计费，`/maestro/tasks` 轮询免费。

单个成片的积分按下式计算：

```
积分 = 成片时长秒 × 0.60 × 场景倍率 + 6 × max(语言数 − 1, 0)
```

Maestro 统一按 **0.60 积分/实际成片秒**计费，支持 5–300 秒、最多 4 种语言和 1080p / 30fps 输出；所有动作与场景均可用。

场景倍率：`drama` 1.35× / `avatar` 1.15× / 其他 1×。

| 示例 | 积分 |
|---|---:|
| Lite 30 秒 | 6 |
| Standard 30 秒 | 18 |
| Standard 60 秒 | 36 |
| Standard 120 秒 | 72 |
| Pro 30 秒 | 36 |
| Pro 300 秒 | 360 |
| 每多一种实际交付语言 | +6 |
| `/maestro/tasks` 轮询 | 免费 |

## 错误处理

在调用 API 时，如果遇到错误，API 会返回相应的错误代码和信息。例如：

- `400 invalid_request`：Bad request, possibly due to a missing `prompt` or invalid parameters.
- `401 invalid_token`：Unauthorized, invalid or missing authorization token.
- `403 forbidden`：Forbidden, insufficient balance or access.
- `429 too_many_requests`：Too many requests, you have exceeded the rate limit.
- `500 api_error`：Internal server error, something went wrong on the server.

### 错误响应示例

```json
{
  "success": false,
  "error": {
    "code": "api_error",
    "message": "fetch failed"
  },
  "trace_id": "2cf86e86-22a4-46e1-ac2f-032c0f2a4e89"
}
```

## 结论

通过本文档，您已经了解了如何使用 Maestro 视频生成 API：只需一句自然语言 `prompt`，即可自动完成脚本、素材、配音、配乐、剪辑、字幕与成片渲染，并支持指定视频类型、风格、音色、多语言输出以及在已有视频上迭代。希望本文档能帮助您更好地对接和使用该 API。如有任何问题，请随时联系我们的技术支持团队。

## 相关接口

- [Maestro 任务查询 API 对接说明](development_maestro_tasks.md)：用 `POST /maestro/videos` 返回的 `task_id` 查询任务状态与结果，或拉取历史任务列表（轮询免费）。
