# Maestro 任务查询 API 对接说明

Maestro 任务查询 API 的主要功能是通过 [Maestro 视频生成 API](development_maestro_videos.md)（`POST /maestro/videos`）返回的任务 ID，查询该任务的执行状态与最终结果。

本文档将详细介绍 Maestro 任务查询 API 的对接说明。由于视频生成是一个异步任务，提交后需要用本接口轮询获取进度与成片，**轮询免费、不消耗积分。**

`POST https://api.acedata.cloud/maestro/tasks`

## 申请流程

要使用 Maestro 任务查询 API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Maestro 任务查询 API →](https://platform.acedata.cloud/documents/maestro-tasks)

## 查询单个任务

关于怎样创建视频任务，请参考文档 [Maestro 视频生成 API](development_maestro_videos.md)。我们以其返回的一个任务 ID 为例：`f57e99c4f60f4373a15517742ce2357d`，演示如何查询它的状态与结果。

### 设置请求头和请求体

**Request Headers** 包括：

- `accept`：指定接收 JSON 格式的响应结果，这里填写为 `application/json`。
- `authorization`：调用 API 的密钥，申请之后可以直接下拉选择。
- `content-type`：请求体的格式，这里填写为 `application/json`。

**Request Body** 包括：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | 查询单个任务时必填 | `POST /maestro/videos` 返回的 `task_id` |
| `action` | string | 否 | `retrieve`（默认，查询单个任务）；查询历史列表时固定为 `retrieve_batch` |

### 代码示例

对应的 CURL 代码如下：

```bash
curl -X POST 'https://api.acedata.cloud/maestro/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "id": "f57e99c4f60f4373a15517742ce2357d",
  "action": "retrieve"
}'
```

对应的 Python 代码如下：

```python
import requests

url = "https://api.acedata.cloud/maestro/tasks"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "id": "f57e99c4f60f4373a15517742ce2357d",
    "action": "retrieve"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

### 响应示例

请求成功后，API 将返回该视频任务的状态与结果。任务完成时的返回示例如下（每种语言对应一个 `variant`）：

```json
{
  "id": "f57e99c4f60f4373a15517742ce2357d",
  "started_at": 1769262721.823,
  "finished_at": 1769264698.3,
  "elapsed": 1976.477,
  "status": "succeeded",
  "progress": {
    "percent": 100,
    "stage": "producing",
    "message": "rendering scene 2"
  },
  "request": {
    "prompt": "用 20 秒讲清楚什么是向量数据库，适合零基础观众，结尾给一句记忆点",
    "langs": [
      "zh-cn",
      "en"
    ],
    "aspect": "9:16",
    "duration": 20
  },
  "response": {
    "success": true,
    "data": {
      "variants": [
        {
          "lang": "zh-cn",
          "aspect": "9:16",
          "kind": "video",
          "title": "什么是向量数据库",
          "output_url": "https://cdn.acedata.cloud/assets/examples/gemini/04a043bd-6b23-4b4e-945c-ce48158c3eee-3a89912507c7.mp4?example=video-001"
        },
        {
          "lang": "en",
          "aspect": "9:16",
          "kind": "video",
          "title": "What is a vector database",
          "output_url": "https://cdn.acedata.cloud/assets/examples/gemini/04a043bd-6b23-4b4e-945c-ce48158c3eee-3a89912507c7.mp4?example=video-002"
        }
      ],
      "project": {
        "tarball_url": null,
        "outputs": [
          "https://…/zh.mp4",
          "https://…/en.mp4"
        ]
      },
      "percent": 100,
      "stage": "producing",
      "progress": [
        {
          "stage": "producing",
          "message": "rendering scene 2",
          "pct": 60,
          "t": 1750000000
        }
      ]
    }
  }
}
```

返回结果的字段介绍如下：

- `id`：此视频任务的 ID，用于唯一标识本次视频生成任务。
- `status`：任务状态，取值为 `pending → planning → producing → succeeded`（或 `failed`）。任务是否已完成，以该顶层 `status` 为准。
- `elapsed`：任务已耗时（秒）。
- `progress`：顶层进度对象，`percent`（0–100）在任务成功后会被兜底为 100；`stage` 与 `message` 反映 AI 导演最近一条进度事件（因此成功后 `stage` 可能仍是最后一个执行阶段如 `producing`），可直接用于展示进度条。
- `request`：发起任务时的请求体。
- `response`：任务的返回信息。
  - `success`：任务是否成功。
  - `data.variants`：每种语言对应一个成片对象，含 `lang`、`aspect`、`title`、`output_url`（成片下载地址）等。
  - `data.project`：整个项目产物，含 `tarball_url`（工程包）与 `outputs`（所有成片链接）。
  - `data.progress`：按阶段追加的进度事件数组（append-only 日志），可用于展示详细的实时进度。
- `created_at`：任务创建时间，Unix 时间戳（秒）。
- `started_at`：任务开始执行时间，Unix 时间戳（秒）。任务尚未开始时为 null。
- `finished_at`：任务完成时间，Unix 时间戳（秒）。任务未完成时为 null。

## 查询历史列表

传入 `action: retrieve_batch` 即可获取当前登录执行者最近的任务（按创建时间倒序），可用于「我的视频」列表页。历史列表按登录身份隔离。

**Request Body** 包括：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `action` | string | 是 | 固定为 `retrieve_batch` |
| `limit` | int | 否 | 返回条数，默认 20；有效范围为 1–100 |
| `created_at_max` | int | 否 | 只返回严格早于该 Unix 时间戳的任务（不含边界值，翻页用） |
| `created_at_min` | int | 否 | 只返回严格晚于该 Unix 时间戳的任务（不含边界值） |

### 代码示例

对应的 CURL 代码如下：

```bash
curl -X POST 'https://api.acedata.cloud/maestro/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "action": "retrieve_batch",
  "limit": 20
}'
```

### 响应示例

请求成功后，API 将返回当前用户的历史任务列表：

```json
{
  "count": 2,
  "items": [
    {
      "id": "f57e99c4f60f4373a15517742ce2357d",
      "started_at": 1769262721.823,
      "finished_at": 1769264698.3,
      "elapsed": 1976.477,
      "status": "succeeded",
      "progress": {
        "percent": 100,
        "stage": "producing",
        "message": "rendering scene 2"
      },
      "request": {
        "prompt": "…",
        "langs": [
          "zh-cn",
          "en"
        ],
        "aspect": "9:16",
        "duration": 20
      },
      "response": {
        "success": true,
        "data": {
          "variants": [
            {
              "lang": "zh-cn",
              "output_url": "https://cdn.acedata.cloud/assets/examples/gemini/04a043bd-6b23-4b4e-945c-ce48158c3eee-3a89912507c7.mp4?example=video-003"
            }
          ]
        }
      }
    }
  ]
}
```

返回结果的字段介绍如下：

- `count`：当前登录执行者可见的任务总数，不受时间条件或 `limit` 影响。
- `items`：经过时间条件与 `limit` 筛选的任务数组，按创建时间倒序排列；每个元素的格式与「查询单个任务」的返回结果一致。

## 轮询建议

由于视频生产耗时较长，`status` 会经历 `pending → planning → producing → succeeded`（或 `failed`）。建议每 5–10 秒轮询一次，直到 `status` 变为 `succeeded` 或 `failed` 为止。可借助顶层 `progress.percent` 展示实时进度条。**轮询本接口免费，不消耗积分。**

## 错误处理

在调用 API 时，如果遇到错误，API 会返回相应的错误代码和信息。例如：

- `401 invalid_token`：Unauthorized, invalid or missing authorization token.
- `404 not_found`：Task not found, the given task_id does not exist.
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

通过本文档，您已经了解了如何使用 Maestro 任务查询 API 查询单个任务的状态与结果，以及拉取当前用户的历史任务列表。希望本文档能帮助您更好地对接和使用该 API。如有任何问题，请随时联系我们的技术支持团队。

## 相关接口

- [Maestro 视频生成 API 对接说明](development_maestro_videos.md)：用一句自然语言提示词自动生产带字幕的成片，提交后返回 `task_id`，再用本接口轮询结果。
