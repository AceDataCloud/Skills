# Nano Banana Tasks API 的对接和使用

Nano Banana Tasks API 的主要功能是通过输入 Nano Banana Images API 生成的任务 ID 来查询该任务的执行情况。

本文档将详细介绍 Nano Banana Tasks API 的对接说明，帮助您轻松集成并充分利用该 API 的强大功能。通过 Nano Banana Tasks API ，您可以轻松实现查询 Nano Banana Images API 的任务执行情况。

## 请求示例

Nano Banana Tasks API 可以用于查询 Nano Banana Images API 的结果。关于怎样使用 Nano Banana Images API，请参考文档 [Nano Banana Images API ](https://platform.acedata.cloud/documents/veo-videos)。

我们以 Nano Banana Images API 服务返回的任务 ID 一个为例，演示如何使用该 API。假设我们有一个任务 ID：4d320ead-4af4-4a55-8f3e-f2afebdf4fd0，接下来演示如何通过传入一个任务 ID 来。

### 任务示例图

<p><img src="https://cdn.acedata.cloud/nuiuth.png" width="500" class="m-auto"></p>

### 设置请求头和请求体

**Request Headers** 包括：

- `accept`：指定接收 JSON 格式的响应结果，这里填写为 `application/json`。
- `authorization`：调用 API 的密钥，申请之后可以直接下拉选择。

**Request Body** 包括：

- `id`：上传的任务 ID。
- `action`：对任务的操作方式。

设置如下图所示：

<p><img src="https://cdn.acedata.cloud/nuiuth.png" width="500" class="m-auto"></p>

### 代码示例

可以发现，在页面右侧已经自动生成了各种语言的代码，如图所示：

<p><img src="https://cdn.acedata.cloud/r1u4vl.png" width="500" class="m-auto"></p>

部分代码示例如下：

#### CURL

```bash
curl -X POST 'https://api.acedata.cloud/nano-banana/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "id": "4d320ead-4af4-4a55-8f3e-f2afebdf4fd0",
  "action": "retrieve"
}'
```

#### Python

```python
import requests

url = "https://api.acedata.cloud/nano-banana/tasks"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "id": "4d320ead-4af4-4a55-8f3e-f2afebdf4fd0",
    "action": "retrieve"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

### 响应示例

请求成功后，API 将返回此处任务的详情信息。例如：

```json
{
  "_id": "68bc7c3c550a4144a53d0e24",
  "id": "4d320ead-4af4-4a55-8f3e-f2afebdf4fd0",
  "api_id": "9d8a117e-31ca-4322-a0fd-1771296ec610",
  "application_id": "8afd681a-2a4e-4265-aecb-43970094c019",
  "created_at": 1757183036.787,
  "started_at": 1757183036.847,
  "finished_at": 1757183048.147,
  "elapsed": 11.3,
  "credential_id": "097b2987-62f4-4ac0-b0cc-aed41e372a07",
  "request": {
    "action": "generate",
    "prompt": "a white siamese cat"
  },
  "trace_id": "7ba1f1e8-0ef8-450d-8bb2-b5c3bf1ea319",
  "type": "images",
  "user_id": "b87f67c1-b04f-4332-99a1-7a5e651331c6",
  "response": {
    "success": true,
    "task_id": "4d320ead-4af4-4a55-8f3e-f2afebdf4fd0",
    "trace_id": "7ba1f1e8-0ef8-450d-8bb2-b5c3bf1ea319",
    "data": [
      {
        "prompt": "a white siamese cat",
        "image_url": "https://platform.cdn.acedata.cloud/nanobanana/7e7bd000-698a-4e14-bb2d-3db61237e4bb.png"
      }
    ]
  }
}
```

返回结果一共有多个字段，request 字段就是发起任务时的 request body，同时 response 字段是任务完成后返回的 response body。字段介绍如下。

- `id`，生成此任务的 ID，用于唯一标识此次生成任务。
- `request`，查询任务中的请求信息。
- `response`，查询任务中的返回信息。
- `created_at`，任务创建时间，Unix 时间戳（秒，浮点）。
- `started_at`，任务开始执行时间，Unix 时间戳（秒，浮点）。
- `finished_at`，任务完成时间，Unix 时间戳（秒，浮点）。任务未完成时不返回该字段。
- `elapsed`，任务执行耗时，单位为秒（浮点，保留 3 位小数）。任务未完成时不返回该字段。

## 批量查询操作

这是是针对多个任务 ID 来进行查询任务详情，与上面不同的是需要将 action 选中为 `retrieve_batch`

**Request Body** 包括：

- `ids`：上传的任务 ID 数组。
- `action`：对任务的操作方式。

示例如下：

```bash
curl -X POST 'https://api.acedata.cloud/nano-banana/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "ids": ["1ebe4f2b-59ba-4385-a4ea-0ce8a3fe12ed","1ebe4f2b-59ba-4385-a4ea-0ce8a3fe12ed"],
  "action": "retrieve_batch"
}'
```

### 响应示例

请求成功后，API 将返回此次所有批量任务的具体详情信息。例如：

```json
{
  "items": [
    {
      "_id": "68bc7c3c550a4144a53d0e24",
      "id": "4d320ead-4af4-4a55-8f3e-f2afebdf4fd0",
      "api_id": "9d8a117e-31ca-4322-a0fd-1771296ec610",
      "application_id": "8afd681a-2a4e-4265-aecb-43970094c019",
      "created_at": 1757183036.787,
      "started_at": 1757183036.847,
      "finished_at": 1757183048.147,
      "elapsed": 11.3,
      "credential_id": "097b2987-62f4-4ac0-b0cc-aed41e372a07",
      "request": {
        "action": "generate",
        "prompt": "a white siamese cat"
      },
      "trace_id": "7ba1f1e8-0ef8-450d-8bb2-b5c3bf1ea319",
      "type": "images",
      "user_id": "b87f67c1-b04f-4332-99a1-7a5e651331c6",
      "response": {
        "success": true,
        "task_id": "4d320ead-4af4-4a55-8f3e-f2afebdf4fd0",
        "trace_id": "7ba1f1e8-0ef8-450d-8bb2-b5c3bf1ea319",
        "data": [
          {
            "prompt": "a white siamese cat",
            "image_url": "https://platform.cdn.acedata.cloud/nanobanana/7e7bd000-698a-4e14-bb2d-3db61237e4bb.png"
          }
        ]
      }
    }
  ],
  "count": 1
}
```

返回结果一共有多个字段，其中 items 是包含了批量任务的具体详情信息，每个任务的具体信息与上文的字段一样，字段信息如下。

- `items`，批量任务的所有具体详情信息。它是一个数组，每个数组的元素和上文查询单个任务的返回结果格式是一样的。
- `count`，此处批量查询任务的个数。

## 错误处理

在调用 API 时，如果遇到错误，API 会返回相应的错误代码和信息。例如：

- `400 token_mismatched`：Bad request, possibly due to missing or invalid parameters.
- `400 api_not_implemented`：Bad request, possibly due to missing or invalid parameters.
- `401 invalid_token`：Unauthorized, invalid or missing authorization token.
- `429 too_many_requests`：Too many requests, you have exceeded the rate limit.
- `403 forbidden`：提供方原生安全策略拒绝了请求或生成结果；若所有生成调用均被拒，任务以失败终态保存，不包含图片且不计费。多图请求中其余成功调用仍可返回并按实际张数计费。
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

通过本文档，您已经了解了如何使用 Nano Banana Tasks API 进行查询单个或批量任务的所有具体详情信息。希望本文档能帮助您更好地对接和使用该 API。如有任何问题，请随时联系我们的技术支持团队。
