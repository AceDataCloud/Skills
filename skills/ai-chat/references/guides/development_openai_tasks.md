# OpenAI Tasks API 接入与使用

OpenAI Tasks API 用于查询此前以 **回调模式** 提交到 OpenAI 图片接口的任务结果。当您无法等待同步 HTTP 响应、或希望事后再次查询任务时，请使用本接口。

回调模式下，**原始的图片接口在受理请求后会立即返回一个 `task_id`**，您直接持有这个 `task_id`、并在需要时拿它到本接口查询即可，无需额外传递自定义 `trace_id`（仅当您希望用自有业务标识做关联时才需要）。

> 仅当原始图片请求中带有 `callback_url` 时，任务才会被持久化。同步（非回调）方式调用的请求不会被存储。

## 申请流程

OpenAI Tasks API 与现有 OpenAI 服务共用授权。如果您已经申请了 OpenAI Images Generations，可直接使用相同的 token 调用本接口，无需额外申请。

新用户首次申请均有免费额度。

## 接口地址

```
POST https://api.acedata.cloud/openai/tasks
```

支持的 `action`：

| 操作 | 说明 |
| --- | --- |
| `retrieve` | 通过 `id` 或 `trace_id` 查询单条任务 |
| `retrieve_batch` | 通过 `ids` / `trace_ids` / `application_id` / `user_id` 批量查询 |

## 请求头

- `accept: application/json`
- `authorization: Bearer {token}`
- `content-type: application/json`

## 单任务查询（`retrieve`）

### 请求体

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `action` | string | 是 | 固定为 `retrieve` |
| `id` | string | 二选一 | 提交图片请求时同步响应里返回的任务 ID（推荐使用） |
| `trace_id` | string | 二选一 | 仅当您在原始请求中显式传入了自定义 `trace_id` 时才需要使用 |

`id` 和 `trace_id` 至少传一个。一般情况下直接使用提交响应中的 `id` 即可，`trace_id` 仅在您希望用自定义业务标识做关联时再传。

### 代码示例

#### CURL

```bash
curl -X POST 'https://api.acedata.cloud/openai/tasks' \
  -H 'accept: application/json' \
  -H 'authorization: Bearer {token}' \
  -H 'content-type: application/json' \
  -d '{
    "action": "retrieve",
    "id": "7489df4c-ef03-4de0-b598-e9a590793434"
  }'
```

#### Python

```python
import requests

url = "https://api.acedata.cloud/openai/tasks"
headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json",
}
payload = {
    "action": "retrieve",
    "id": "7489df4c-ef03-4de0-b598-e9a590793434",
}
response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

### 返回示例

任务存在时：

```json
{
  "_id": "67a1b2c3d4e5f6a7b8c9d0e1",
  "id": "7489df4c-ef03-4de0-b598-e9a590793434",
  "trace_id": "my-custom-trace-001",
  "type": "images",
  "application_id": "9dec7b2a-1cad-41ff-8536-d4ddaf2525d4",
  "user_id": "5d8e7f6a-1234-4abc-9def-0123456789ab",
  "credential_id": "68253cc8-505d-47f4-97ad-0050a62e4975",
  "created_at": 1763142607.967,
  "started_at": 1763142607.97,
  "finished_at": 1763142637.404,
  "elapsed": 29.437,
  "request": {
    "model": "gpt-image-1",
    "prompt": "A cat sitting on a table",
    "size": "1024x1024",
    "callback_url": "https://your.server/callback"
  },
  "response": {
    "created": 1763142637,
    "data": [
      { "url": "https://platform.cdn.acedata.cloud/openai/...png" }
    ],
    "success": true
  }
}
```

未匹配到任何任务时返回空对象：

```json
{}
```

### 字段说明

- `id`：原始图片请求受理时生成的任务 ID。
- `trace_id`：原始请求中传入的自定义追踪标识，便于客户端业务做关联。
- `type`：任务类型。`gpt-image` 系列（如 `gpt-image-2`）写入的任务为 `images`；`gpt-image-1`、nano-banana 等使用 `images_generations` / `images_edits`，部分聊天接口为 `chat_completions_image`。
- `request`：原始请求的完整请求体。
- `response`：回调完成时返回的最终响应体。
- `created_at` / `started_at` / `finished_at`：Unix 时间戳（秒，浮点）。
- `elapsed`：执行耗时（秒，浮点）。
- `application_id` / `user_id` / `credential_id`：所属应用、终端用户、凭据 ID。

## 批量查询（`retrieve_batch`）

### 请求体

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `action` | string | 固定为 `retrieve_batch` |
| `ids` | string[] | 按任务 ID 列表查询 |
| `trace_ids` | string[] | 按 `trace_id` 列表查询 |
| `application_id` | string | 按应用查询所有任务 |
| `user_id` | string | 按终端用户查询所有任务 |
| `type` | string | 按任务类型过滤（取值：`images`、`images_generations`、`images_edits`） |
| `offset` | int | 分页起点，默认 `0` |
| `limit` | int | 单页条数，默认 `12` |
| `created_at_min` | float | 起始时间戳（Unix 秒） |
| `created_at_max` | float | 截止时间戳（Unix 秒） |

`ids` / `trace_ids` / `application_id` / `user_id` 或 `created_at_*` 时间窗口择一传入即可。

### CURL 示例

```bash
curl -X POST 'https://api.acedata.cloud/openai/tasks' \
  -H 'authorization: Bearer {token}' \
  -H 'content-type: application/json' \
  -d '{
    "action": "retrieve_batch",
    "trace_ids": ["my-trace-001", "my-trace-002"]
  }'
```

### 返回示例

```json
{
  "items": [
    {
      "_id": "67a1b2c3d4e5f6a7b8c9d0e1",
      "id": "7489df4c-ef03-4de0-b598-e9a590793434",
      "trace_id": "my-trace-001",
      "type": "images",
      "request": {
        "model": "gpt-image-2",
        "prompt": "A cat"
      },
      "response": {
        "data": [
          {
            "url": "https://...png"
          }
        ]
      },
      "created_at": 1763142607.967,
      "started_at": 1763142608.027,
      "finished_at": 1763142637.404,
      "elapsed": 29.377
    }
  ],
  "count": 1
}
```

## 端到端示例：提交并轮询

Tasks API 主要服务于回调模式下的异步流程。回调模式下，提交接口会**立即同步返回一个 `task_id`**（即任务 ID），之后您只需直接拿这个 `task_id` 去 Tasks 接口轮询即可，无需自己再生成 `trace_id`。

```python
import os, time, requests

API = "https://api.acedata.cloud"
HEADERS = {
    "authorization": f"Bearer {os.environ['ACEDATA_API_KEY']}",
    "content-type": "application/json",
}

# 1. 提交图片生成任务（callback 模式：带上 callback_url 即可立即返回 task_id）
submit = requests.post(
    f"{API}/openai/images/generations",
    headers=HEADERS,
    json={
        "model": "gpt-image-1",
        "prompt": "一只水彩风格的猫坐在桌子上",
        "callback_url": "https://webhook.site/your-uuid",
    },
).json()
print("submitted:", submit)

task_id = submit["task_id"]

# 2. 直接用提交响应中的 task_id 轮询 Tasks 接口，直到任务完成
while True:
    task = requests.post(
        f"{API}/openai/tasks",
        headers=HEADERS,
        json={"action": "retrieve", "id": task_id},
    ).json()
    if task and task.get("response"):
        print("finished:", task["response"])
        break
    time.sleep(3)
```

## 注意事项

- Tasks 接口本身**不计费**，可以放心轮询。仅原始的图片生成/编辑请求会扣费。
- 仅当原始请求包含 `callback_url` 时，才会写入任务记录；同步调用不会产生可查询的任务。
- 超过平台保留期的任务记录可能被清理。
