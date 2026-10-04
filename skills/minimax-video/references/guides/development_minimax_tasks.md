# MiniMax H3 任务查询 API 对接指南

本文介绍 MiniMax H3 任务查询 API 的对接与使用。该接口用于查询、批量列出或删除 [MiniMax H3 视频生成 API](/documents/minimax-videos-integration) 创建的异步任务。

## 申请流程

要使用 MiniMax H3 任务查询 API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[MiniMax H3 任务查询 API →](https://platform.acedata.cloud/documents/minimax-tasks-integration)

查询任务时应使用创建该任务的同一个 Token。建议将 Token 保存为环境变量，不要写入源码或提交到版本库：

```bash
export ACEDATACLOUD_API_KEY="YOUR_API_KEY"
```

## 接口概览

- **Base URL**：`https://api.acedata.cloud`
- **Endpoint**：`POST /minimax/tasks`
- **认证方式**：HTTP Header 中携带 `authorization: Bearer {token}`
- **请求头**：

  - `accept: application/json`
  - `content-type: application/json`

- **查询单个任务**：`action=retrieve`，传入 `id`
- **批量查询任务**：`action=retrieve_batch`，可按任务 ID、时间范围和分页条件筛选
- **删除任务**：`action=delete`，传入 `id`
- **计费说明**：任务查询免费，不会产生重复计费

创建视频后必须保存 `task_id`。推荐每隔约 10 秒查询一次，直到任务进入终态。

## 请求参数

| 参数 | 类型 | 必填 | 适用动作 | 说明 |
| --- | --- | --- | --- | --- |
| `action` | string | 否 | 全部 | `retrieve`、`retrieve_batch` 或 `delete`；默认 `retrieve` |
| `id` | string | 条件必填 | `retrieve`、`delete` | 单个任务 ID |
| `ids` | string[] | 否 | `retrieve_batch` | 只返回指定任务 ID；省略时按其他条件列出任务 |
| `limit` | integer | 否 | `retrieve_batch` | 本次最多返回的任务数量 |
| `offset` | integer | 否 | `retrieve_batch` | 从结果列表中跳过的任务数量，用于分页 |
| `created_at_min` | number | 否 | `retrieve_batch` | 创建时间下限，Unix 时间戳，单位为秒 |
| `created_at_max` | number | 否 | `retrieve_batch` | 创建时间上限，Unix 时间戳，单位为秒 |

三种动作的用途如下：

| `action` | 用途 | 必要参数 | 响应结构 |
| --- | --- | --- | --- |
| `retrieve` | 查询一个任务的状态和结果 | `id` | `{ "task": {...} }` |
| `retrieve_batch` | 按任务 ID、时间和分页条件批量查询 | 可选 `ids`、时间范围、`offset`、`limit` | `{ "items": [...], "total": number }` |
| `delete` | 根据任务当前状态取消或删除任务记录 | `id` | `{ "id": "...", "deleted": true }` |

## 查询单个任务

```bash
curl -X POST 'https://api.acedata.cloud/minimax/tasks' \
  -H "Authorization: Bearer $ACEDATACLOUD_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "action": "retrieve",
    "id": "f5977217-ed2c-40da-adbe-93d08235618f"
  }'
```

下面是一次真实成功任务的响应：

```json
{
  "task": {
    "id": "f5977217-ed2c-40da-adbe-93d08235618f",
    "model": "MiniMax-H3",
    "status": "succeeded",
    "created_at": 1786184658,
    "updated_at": 1786184758,
    "content": {
      "url": "https://cdn.acedata.cloud/assets/examples/minimax/f5977217-ed2c-40da-adbe-93d08235618f-b080c998dde2.mp4"
    },
    "resolution": "768P",
    "duration": 4,
    "usage": {
      "total_seconds": 4,
      "input_seconds": 0,
      "output_seconds": 4,
      "input_image_count": 0
    },
    "ratio": "16:9",
    "task_type": "generation",
    "modality": "video"
  }
}
```

[打开这次任务的真实视频结果](https://cdn.acedata.cloud/assets/examples/minimax/f5977217-ed2c-40da-adbe-93d08235618f-b080c998dde2.mp4)

## 任务状态

| `status` | 含义 | 客户端处理 |
| --- | --- | --- |
| `queued` | 已进入队列，等待执行 | 继续轮询 |
| `running` | 正在生成 | 继续轮询 |
| `succeeded` | 生成成功 | 读取 `task.content.url`，停止轮询 |
| `failed` | 生成失败 | 读取 `task.error`，停止轮询 |
| `cancelled` | 任务已取消 | 停止轮询 |

`succeeded`、`failed` 和 `cancelled` 都是终态。不要在进入终态后继续轮询。

## task 响应字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string | 任务 ID |
| `model` | string | 任务使用的模型，当前为 `MiniMax-H3` |
| `status` | string | 当前任务状态 |
| `error.code` | string | 失败错误码，仅失败时返回 |
| `error.message` | string | 失败原因，仅失败时返回 |
| `created_at` | integer | 创建时间，Unix 时间戳，单位为秒 |
| `updated_at` | integer | 最近一次状态更新时间，Unix 时间戳，单位为秒 |
| `content.url` | string | 成功后的视频地址 |
| `resolution` | string | 输出分辨率，`768P` 或 `2K` |
| `duration` | integer | 输出视频时长，单位为秒 |
| `usage.total_seconds` | integer | 总计费用量，等于输入视频秒数与输出秒数之和 |
| `usage.input_seconds` | integer | 参考视频输入产生的计费用量 |
| `usage.output_seconds` | integer | 输出视频产生的计费用量 |
| `usage.input_image_count` | integer | 计费统计中的输入图片数量 |
| `ratio` | string | 实际输出宽高比；使用 `adaptive` 时以这里的结果为准 |
| `task_type` | string | 视频生成任务为 `generation` |
| `modality` | string | 视频任务为 `video` |

## Python 轮询完整示例

以下代码从环境变量读取 Token，创建任务后每隔 10 秒查询一次：

```python
import os
import time

import requests


BASE_URL = "https://api.acedata.cloud"
HEADERS = {
    "Authorization": f"Bearer {os.environ['ACEDATACLOUD_API_KEY']}",
    "Content-Type": "application/json",
}

create_response = requests.post(
    f"{BASE_URL}/minimax/videos",
    headers=HEADERS,
    json={
        "model": "MiniMax-H3",
        "content": [
            {
                "type": "text",
                "text": "清晨的海边，一艘白色帆船驶过平静海面，镜头缓慢横移",
            }
        ],
        "resolution": "768P",
        "duration": 4,
        "ratio": "16:9",
    },
    timeout=30,
)
create_response.raise_for_status()
task_id = create_response.json()["task_id"]

while True:
    time.sleep(10)
    query_response = requests.post(
        f"{BASE_URL}/minimax/tasks",
        headers=HEADERS,
        json={"action": "retrieve", "id": task_id},
        timeout=30,
    )
    query_response.raise_for_status()
    task = query_response.json()["task"]
    print(f"task={task_id} status={task['status']}")

    if task["status"] == "succeeded":
        print(f"video_url={task['content']['url']}")
        break
    if task["status"] in ("failed", "cancelled"):
        raise RuntimeError(task.get("error") or task["status"])
```

生产环境应为轮询设置总超时，并对 `429` 和临时 `5xx` 使用指数退避。网络超时不等于生成失败，可以使用同一个 `task_id` 继续查询。

## 批量查询

指定多个任务 ID：

```bash
curl -X POST 'https://api.acedata.cloud/minimax/tasks' \
  -H "Authorization: Bearer $ACEDATACLOUD_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "action": "retrieve_batch",
    "ids": ["TASK_ID_1", "TASK_ID_2"],
    "offset": 0,
    "limit": 20
  }'
```

按时间范围分页列出任务：

```json
{
  "action": "retrieve_batch",
  "created_at_min": 1786000000,
  "created_at_max": 1786200000,
  "offset": 0,
  "limit": 20
}
```

批量响应中的 `items` 使用与单任务查询相同的 task 字段，`total` 是筛选条件匹配的任务总数：

```json
{
  "items": [
    {
      "id": "TASK_ID_1",
      "model": "MiniMax-H3",
      "status": "running",
      "resolution": "2K",
      "duration": 5,
      "ratio": "adaptive",
      "task_type": "generation",
      "modality": "video"
    }
  ],
  "total": 1
}
```

任务查询窗口为最近 7 天。超过该窗口的 `task_id` 可能返回无效任务；业务系统应在创建任务时保存 ID，并在成功后及时持久化结果 URL。

## 取消或删除任务

```bash
curl -X POST 'https://api.acedata.cloud/minimax/tasks' \
  -H "Authorization: Bearer $ACEDATACLOUD_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "action": "delete",
    "id": "YOUR_TASK_ID"
  }'
```

动作取决于任务当前状态：

| 当前状态 | 行为 |
| --- | --- |
| `queued` | 取消尚未开始的任务 |
| `succeeded` | 删除任务记录 |
| `failed` | 删除任务记录 |
| `running` | 不允许删除或取消，返回错误 |
| `cancelled` | 不允许重复操作，返回错误 |

删除成功示例：

```json
{
  "id": "YOUR_TASK_ID",
  "deleted": true
}
```

删除任务记录不会撤销已经完成的计费，也不能保证已保存的视频副本同时被删除。

## 失败响应与排查

失败任务仍以 HTTP 200 返回 task 对象，并在 `task.error` 中给出原因：

```json
{
  "task": {
    "id": "YOUR_TASK_ID",
    "model": "MiniMax-H3",
    "status": "failed",
    "error": {
      "code": "1026",
      "message": "video description contains sensitive content"
    },
    "task_type": "generation",
    "modality": "video"
  }
}
```

接口本身返回 `400` 时应检查 `action` 与条件参数，`401` 表示 Token 无效，`429` 表示查询过于频繁，`500` 表示服务暂时不可用。生成失败的任务不计费；成功任务按最终 `usage` 记录用量。
