# Gemini Tasks API 的对接和使用

Gemini Tasks API 的主要功能是通过输入 Gemini Videos Generation API 生成的任务 ID 来查询该任务的执行情况。

本文档将详细介绍 Gemini Tasks API 的对接说明，帮助您轻松集成并查询 Gemini Videos Generation API 的任务执行情况。

## 申请流程

要使用 Gemini Videos Generation API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Gemini Videos Generation API →](https://platform.acedata.cloud/documents/gemini-videos)

## 请求示例

Gemini Tasks API 可以用于查询 Gemini Videos Generation API 的结果。

### 设置请求头和请求体

**Request Headers** 包括：

- `accept`：指定接收 JSON 格式的响应结果，这里填写为 `application/json`。
- `authorization`：调用 API 的密钥，申请之后可以直接下拉选择。

**Request Body** 包括：

- `id`：要查询的任务 ID。
- `action`：对任务的操作方式，单个查询填写 `retrieve`。

### CURL 代码示例

```bash
curl -X POST 'https://api.acedata.cloud/gemini/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "id": "b8976e18-32dc-4718-9ed8-1ea090fcb6ea",
  "action": "retrieve"
}'
```

### 响应示例

请求成功后，API 将返回此处任务的详情信息。其中 `request` 字段是发起任务时的 request body，`response` 字段是任务完成后返回的 response body，例如：

```json
{
  "id": "b8976e18-32dc-4718-9ed8-1ea090fcb6ea",
  "started_at": 1769262721.823,
  "finished_at": 1769262730.723,
  "elapsed": 8.9,
  "request": {
    "prompt": "A cinematic shot of a kitten chasing a butterfly in a sunlit garden",
    "model": "omni-flash",
    "aspect_ratio": "16:9"
  },
  "type": "videos",
  "response": {
    "success": true,
    "task_id": "b8976e18-32dc-4718-9ed8-1ea090fcb6ea",
    "trace_id": "fb751e1e-4705-49ea-9fd4-5024b7865ea2",
    "data": [
      {
        "id": "omni-flash:job_01k777hjrbfrgs2060q5zvf2a5",
        "video_url": "https://cdn.acedata.cloud/gemini/example-video.mp4",
        "state": "succeeded"
      }
    ]
  }
}
```

字段介绍如下：

- `id`：生成任务的 ID，用于唯一标识此次生成任务。
- `request`：查询任务中的请求信息。
- `response`：查询任务中的返回信息。
- `created_at`：任务创建时间，Unix 时间戳（秒，浮点）。
- `started_at`：任务开始执行时间，Unix 时间戳（秒，浮点）。
- `finished_at`：任务完成时间，Unix 时间戳（秒，浮点）。任务未完成时不返回该字段。
- `elapsed`：任务执行耗时，单位为秒（浮点，保留 3 位小数）。任务未完成时不返回该字段。

## 批量查询操作

针对多个任务 ID 查询任务详情时，将 `action` 设置为 `retrieve_batch`，并通过 `ids` 传入任务 ID 数组：

**Request Body** 包括：

- `ids`：要查询的任务 ID 数组。
- `action`：对任务的操作方式，批量查询填写 `retrieve_batch`。

```bash
curl -X POST 'https://api.acedata.cloud/gemini/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "ids": ["b8976e18-32dc-4718-9ed8-1ea090fcb6ea"],
  "action": "retrieve_batch"
}'
```
