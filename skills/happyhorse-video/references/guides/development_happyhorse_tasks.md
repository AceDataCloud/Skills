# HappyHorse Tasks API 的对接和使用

HappyHorse Tasks API 用于查询 HappyHorse Videos API 创建的视频生成或编辑任务。

## 申请流程

要使用 HappyHorse Videos API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[HappyHorse Videos API →](https://platform.acedata.cloud/documents/happyhorse-videos)

## 请求示例

HappyHorse Tasks API 可以用于查询 HappyHorse Videos API 的结果。

### 设置请求头和请求体

**Request Headers** 包括：

- `accept`：指定接收 JSON 格式的响应结果，这里填写为 `application/json`。
- `authorization`：调用 API 的密钥，申请之后可以直接下拉选择。

**Request Body** 包括：

- `id`：要查询的任务 ID。
- `action`：对任务的操作方式，单个查询填写 `retrieve`。

### CURL 代码示例

```bash
curl -X POST 'https://api.acedata.cloud/happyhorse/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "id": "b8976e18-32dc-4718-9ed8-1ea090fcb6ea",
  "action": "retrieve"
}'
```

### 响应示例

请求成功后，API 将返回该任务的详情。其中 `request` 字段是创建任务时的请求体，`response` 字段是任务完成后返回的响应体，例如：

```json
{
  "id": "b8976e18-32dc-4718-9ed8-1ea090fcb6ea",
  "started_at": 1769262721.823,
  "finished_at": 1769262774.423,
  "elapsed": 52.6,
  "request": {
    "action": "generate",
    "model": "happyhorse-1.1-t2v",
    "prompt": "A cinematic shot of a white horse running across a moonlit beach",
    "resolution": "720P",
    "duration": 5
  },
  "type": "videos",
  "response": {
    "success": true,
    "task_id": "b8976e18-32dc-4718-9ed8-1ea090fcb6ea",
    "trace_id": "fb751e1e-4705-49ea-9fd4-5024b7865ea2",
    "data": [
      {
        "id": "1469cfc3-3004-4d9e-ab10-xxxxxx",
        "video_url": "https://cdn.acedata.cloud/happyhorse/c8cbf53aa0.mp4",
        "state": "succeeded",
        "duration": 5,
        "resolution": "720P",
        "ratio": "16:9"
      }
    ]
  }
}
```

字段介绍如下：

- `id`：生成任务的 ID，用于唯一标识此次生成任务。
- `request`：创建任务时的请求信息。
- `response`：任务当前或最终的返回信息。
- `created_at`：任务创建时间，Unix 时间戳（秒，浮点）。
- `started_at`：任务开始执行时间，Unix 时间戳（秒，浮点）。
- `finished_at`：任务完成时间，Unix 时间戳（秒，浮点）。任务未完成时不返回该字段。
- `elapsed`：任务执行耗时，单位为秒（浮点，保留 3 位小数）。任务未完成时不返回该字段。

## 批量查询操作

针对多个任务 ID 查询任务详情时，将 `action` 设置为 `retrieve_batch`，并通过 `ids` 传入任务 ID 数组：

```bash
curl -X POST 'https://api.acedata.cloud/happyhorse/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "ids": ["b8976e18-32dc-4718-9ed8-1ea090fcb6ea"],
  "action": "retrieve_batch"
}'
```

返回结果中会包含 `items` 和 `count` 字段，`items` 为任务详情数组，`count` 为本次匹配到的任务数量。
