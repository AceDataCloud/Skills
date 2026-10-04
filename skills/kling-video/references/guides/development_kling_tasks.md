# Kling Tasks API 的对接和使用

Kling Tasks API 的主要功能是通过输入 Kling Videos Generation API 生成的任务ID来查询该任务的执行情况。

本文档将详细介绍 Kling Tasks API 的对接说明，帮助您轻松集成并充分利用该 API 的强大功能。通过 Kling Tasks API ，您可以轻松实现查询 Kling Videos Generation API 的任务执行情况。

## 申请流程

要使用 Kling Videos Generation API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Kling Videos Generation API →](https://platform.acedata.cloud/documents/kling-videos)

## 请求示例

Kling Tasks API 可以用于查询 Kling Videos Generation API 的结果。关于怎样使用 Kling Videos Generation API，请参考文档 [Kling Videos Generation API ](https://platform.acedata.cloud/documents/kling-videos)。

我们以 Kling Videos Generation API 服务返回的任务ID一个为例，演示如何使用该 API。假设我们有一个任务ID：20068983-0cc9-4c6a-aeb6-9c6a3c668be0，接下来演示如何通过传入一个任务ID来。

### 任务示例图

<p><img src="https://cdn.acedata.cloud/om6p6g.png" width="500" class="m-auto"></p>

### 设置请求头和请求体

**Request Headers** 包括：

- `accept`：指定接收 JSON 格式的响应结果，这里填写为 `application/json`。
- `authorization`：调用 API 的密钥，申请之后可以直接下拉选择。

**Request Body** 包括：

- `id`：上传的任务ID。
- `action`：对任务的操作方式。

设置如下图所示：

<p><img src="https://cdn.acedata.cloud/xztiqi.png" width="500" class="m-auto"></p>

### 代码示例

可以发现，在页面右侧已经自动生成了各种语言的代码，如图所示：

<p><img src="https://cdn.acedata.cloud/bsqh3i.png" width="500" class="m-auto"></p>

部分代码示例如下：

#### CURL

```bash
curl -X POST 'https://api.acedata.cloud/kling/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "id": "20068983-0cc9-4c6a-aeb6-9c6a3c668be0",
  "action": "retrieve"
}'
```

#### Python

```python
import requests

url = "https://api.acedata.cloud/kling/tasks"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "id": "20068983-0cc9-4c6a-aeb6-9c6a3c668be0",
    "action": "retrieve"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

### 响应示例

请求成功后，API 将返回此处视频任务的详情信息。例如：

```json
{
  "_id": "67c5163f550a4144a5b68698",
  "id": "20068983-0cc9-4c6a-aeb6-9c6a3c668be0",
  "api_id": "29187cb2-1acb-43b8-baf5-3f3f709292eb",
  "application_id": "f35762fe-e8a4-4613-bb70-e5c1be4f9fc2",
  "created_at": 1740969535.333,
  "started_at": 1740969535.393,
  "finished_at": 1740969852.463,
  "elapsed": 317.07,
  "credential_id": "ce81345f-7e2a-4871-b539-aefb5f725220",
  "request": {
    "action": "text2video",
    "model": "kling-v1",
    "prompt": "White ceramic coffee mug on glossy marble countertop with morning window light. Camera slowly rotates 360 degrees around the mug, pausing briefly at the handle.",
    "callback_url": "https://webhook.site/624b2c78-6dbd-4618-9d2b-b32eade6d8c3"
  },
  "trace_id": "0a907f69-4ae2-4a08-b34c-ee15c1c47077",
  "type": "videos",
  "user_id": "ad7afe47-cea9-4cda-980f-2ad8810e51cf",
  "job_id": "CjJzzGfBfqcAAAAAAKdVMQ",
  "response": {
    "success": true,
    "video_id": "030bb06d-98d4-4044-9042-0aa0822e8c8c",
    "video_url": "https://cdn.acedata.cloud/assets/examples/gemini/04a043bd-6b23-4b4e-945c-ce48158c3eee-3a89912507c7.mp4",
    "duration": "5.1",
    "state": "succeed",
    "task_id": "20068983-0cc9-4c6a-aeb6-9c6a3c668be0"
  }
}
```

返回结果一共有多个字段，request 字段就是发起任务时的 request body，同时response 字段是任务完成后返回的response body。字段介绍如下。

- `id`，生成此视频任务的 ID，用于唯一标识此次视频生成任务。
- `request`，查询视频任务中的请求信息。
- `response`，查询视频任务中的返回信息。
- `created_at`，任务创建时间，Unix 时间戳（秒，浮点）。
- `started_at`，任务开始执行时间，Unix 时间戳（秒，浮点）。
- `finished_at`，任务完成时间，Unix 时间戳（秒，浮点）。任务未完成时不返回该字段。
- `elapsed`，任务执行耗时，单位为秒（浮点，保留 3 位小数）。任务未完成时不返回该字段。

## 批量查询操作

这是是针对多个任务ID来进行查询视频任务详情，与上面不同的是需要将action选中为retrieve_batch

**Request Body** 包括：

- `ids`：上传的任务ID数组。
- `action`：对任务的操作方式。

设置如下图所示：

<p><img src="https://cdn.acedata.cloud/4p5uvq.png" width="500" class="m-auto"></p>

### 代码示例

可以发现，在页面右侧已经自动生成了各种语言的代码，如图所示：

<p><img src="https://cdn.acedata.cloud/g3b7g6.png" width="500" class="m-auto"></p>

部分代码示例如下：

#### CURL

```bash
curl -X POST 'https://api.acedata.cloud/kling/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "ids": ["e3a575aa-a4bd-49c8-9b12-cde38d5462e0","20068983-0cc9-4c6a-aeb6-9c6a3c668be0"],
  "action": "retrieve_batch"
}'
```

### 响应示例

请求成功后，API 将返回此次所有批量视频任务的具体详情信息。例如：

```json
{
  "items": [
    {
      "_id": "67c5163f550a4144a5b68698",
      "id": "20068983-0cc9-4c6a-aeb6-9c6a3c668be0",
      "api_id": "29187cb2-1acb-43b8-baf5-3f3f709292eb",
      "application_id": "f35762fe-e8a4-4613-bb70-e5c1be4f9fc2",
      "created_at": 1740969535.333,
      "started_at": 1740969535.393,
      "finished_at": 1740969852.463,
      "elapsed": 317.07,
      "credential_id": "ce81345f-7e2a-4871-b539-aefb5f725220",
      "request": {
        "action": "text2video",
        "model": "kling-v1",
        "prompt": "White ceramic coffee mug on glossy marble countertop with morning window light. Camera slowly rotates 360 degrees around the mug, pausing briefly at the handle.",
        "callback_url": "https://webhook.site/624b2c78-6dbd-4618-9d2b-b32eade6d8c3"
      },
      "trace_id": "0a907f69-4ae2-4a08-b34c-ee15c1c47077",
      "type": "videos",
      "user_id": "ad7afe47-cea9-4cda-980f-2ad8810e51cf",
      "job_id": "CjJzzGfBfqcAAAAAAKdVMQ",
      "response": {
        "success": true,
        "video_id": "030bb06d-98d4-4044-9042-0aa0822e8c8c",
        "video_url": "https://cdn.acedata.cloud/assets/examples/gemini/04a043bd-6b23-4b4e-945c-ce48158c3eee-3a89912507c7.mp4",
        "duration": "5.1",
        "state": "succeed",
        "task_id": "20068983-0cc9-4c6a-aeb6-9c6a3c668be0"
      }
    },
    {
      "_id": "67c51415550a4144a5b442a5",
      "id": "e3a575aa-a4bd-49c8-9b12-cde38d5462e0",
      "api_id": "29187cb2-1acb-43b8-baf5-3f3f709292eb",
      "application_id": "f35762fe-e8a4-4613-bb70-e5c1be4f9fc2",
      "created_at": 1740968981.619,
      "started_at": 1740968981.679,
      "finished_at": 1740969297.937,
      "elapsed": 316.258,
      "credential_id": "ce81345f-7e2a-4871-b539-aefb5f725220",
      "request": {
        "action": "text2video",
        "model": "kling-v1",
        "prompt": "White ceramic coffee mug on glossy marble countertop with morning window light. Camera slowly rotates 360 degrees around the mug, pausing briefly at the handle."
      },
      "trace_id": "4f32ba2d-8846-4ea9-9253-997ec0b2e052",
      "type": "videos",
      "user_id": "ad7afe47-cea9-4cda-980f-2ad8810e51cf",
      "job_id": "Cjil4mfBfs0AAAAAAKbMQQ",
      "response": {
        "success": true,
        "video_id": "af9a1af0-9aa0-4638-81c1-d41d6143c508",
        "video_url": "https://cdn.acedata.cloud/assets/examples/gemini/04a043bd-6b23-4b4e-945c-ce48158c3eee-3a89912507c7.mp4",
        "duration": "5.1",
        "state": "succeed",
        "task_id": "e3a575aa-a4bd-49c8-9b12-cde38d5462e0"
      }
    }
  ],
  "count": 2
}
```

返回结果一共有多个字段，其中items是包含了批量视频任务的具体详情信息，每个视频任务的具体信息与上文的字段一样，字段信息如下。

- `items`，批量视频任务的所有具体详情信息。它是一个数组，每个数组的元素和上文查询单个任务的返回结果格式是一样的。
- `count`，此处批量查询视频任务的个数。

## 错误处理

在调用 API 时，如果遇到错误，API 会返回相应的错误代码和信息。例如：

- `400 token_mismatched`：Bad request, possibly due to missing or invalid parameters.
- `400 api_not_implemented`：Bad request, possibly due to missing or invalid parameters.
- `401 invalid_token`：Unauthorized, invalid or missing authorization token.
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

通过本文档，您已经了解了如何使用 Kling Tasks API 进行查询单个或批量视频任务的所有具体详情信息。希望本文档能帮助您更好地对接和使用该 API。如有任何问题，请随时联系我们的技术支持团队。
