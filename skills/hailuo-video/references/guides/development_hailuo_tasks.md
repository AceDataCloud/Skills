# Hailuo Tasks API 的对接和使用

Hailuo Tasks API 的主要功能是通过输入 Hailuo Videos Generation API 生成的任务ID来查询该任务的执行情况。


本文档将详细介绍  Hailuo Tasks API  的对接说明，帮助您轻松集成并充分利用该 API 的强大功能。通过  Hailuo Tasks API ，您可以轻松实现查询  Hailuo Videos Generation API 的任务执行情况。

## 申请流程

要使用 Hailuo Videos Generation API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Hailuo Videos Generation API →](https://platform.acedata.cloud/documents/hailuo-videos-integration)

## 请求示例
Hailuo Tasks API 可以用于查询 Hailuo Videos Generation API 的结果。关于怎样使用 Hailuo Videos Generation API，请参考文档 [Hailuo Videos Generation API ](https://platform.acedata.cloud/documents/hailuo-videos-generation-integration)。

我们以 Hailuo Videos Generation API 服务返回的任务ID一个为例，演示如何使用该 API。假设我们有一个任务ID：58cc618b-9639-4ee7-add2-d2fcf260d9a3，接下来演示如何通过传入一个任务ID来。

### 任务示例图

<p><img src="https://cdn.acedata.cloud/4f9d95.png" width="500" class="m-auto"></p>

### 设置请求头和请求体

**Request Headers** 包括：

- `accept`：指定接收 JSON 格式的响应结果，这里填写为 `application/json`。
- `authorization`：调用 API 的密钥，申请之后可以直接下拉选择。

**Request Body** 包括：

- `id`：上传的任务ID。
- `action`：对任务的操作方式。

设置如下图所示：

<p><img src="https://cdn.acedata.cloud/e9btl5.png" width="500" class="m-auto"></p>

### 代码示例

可以发现，在页面右侧已经自动生成了各种语言的代码，如图所示：

<p><img src="https://cdn.acedata.cloud/tfn261.png" width="500" class="m-auto"></p>

部分代码示例如下：

#### CURL

```bash
curl -X POST 'https://api.acedata.cloud/hailuo/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "id": "58cc618b-9639-4ee7-add2-d2fcf260d9a3",
  "action": "retrieve"
}'
```

#### Python

```python
import requests

url = "https://api.acedata.cloud/hailuo/tasks"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "id": "58cc618b-9639-4ee7-add2-d2fcf260d9a3",
    "action": "retrieve"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

### 响应示例

请求成功后，API 将返回此处视频任务的详情信息。例如：

```json
{
  "_id": "67866dff550a4144a5867aa7",
  "id": "58cc618b-9639-4ee7-add2-d2fcf260d9a3",
  "api_id": "d5af91f6-a7ec-4015-b0a5-d25051158470",
  "application_id": "2f9f4d93-9193-4c49-a1a5-eddf0ff38abb",
  "created_at": 1736863231.588,
  "started_at": 1736863231.648,
  "finished_at": 1736863300.748,
  "elapsed": 69.1,
  "credential_id": "f634e655-012e-432e-92a8-a87e4a80d636",
  "request": {
    "action": "generate",
    "prompt": "Internal heat"
  },
  "trace_id": "0c1f9f13-0aef-4d9a-a9d2-1d27055ff190",
  "user_id": "ad7afe47-cea9-4cda-980f-2ad8810e51cf",
  "response": {
    "success": true,
    "task_id": "58cc618b-9639-4ee7-add2-d2fcf260d9a3",
    "trace_id": "0c1f9f13-0aef-4d9a-a9d2-1d27055ff190",
    "data": [
      {
        "id": "2a1tbgnjdxrg80cmcmes19s33r",
        "model": "minimax-t2v",
        "prompt": "Internal heat",
        "first_image_url": null,
        "video_url": "https://platform.cdn.acedata.cloud/czjl/tjU3QYKgU96IJFgpL0eMfBFhmy0qXz9Y05P2IBhShCYaDCFUA/tmp5uligw3a.output.mp4",
        "state": "succeeded"
      }
    ]
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

<p><img src="https://cdn.acedata.cloud/i023y9.png" width="500" class="m-auto"></p>

### 代码示例

可以发现，在页面右侧已经自动生成了各种语言的代码，如图所示：

<p><img src="https://cdn.acedata.cloud/3sxeeh.png" width="500" class="m-auto"></p>

部分代码示例如下：

#### CURL

```bash
curl -X POST 'https://api.acedata.cloud/hailuo/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "ids": ["09d4a93e-d5c8-4778-bdf2-711773d71c59","58cc618b-9639-4ee7-add2-d2fcf260d9a3"],
  "action": "retrieve_batch"
}'
```

#### Python

```python
import requests

url = "https://api.acedata.cloud/hailuo/tasks"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "ids": ["09d4a93e-d5c8-4778-bdf2-711773d71c59","58cc618b-9639-4ee7-add2-d2fcf260d9a3"],
    "action": "retrieve_batch"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

### 响应示例

请求成功后，API 将返回此次所有批量视频任务的具体详情信息。例如：

```json
{
  "items": [
    {
      "_id": "67866fad550a4144a587053c",
      "id": "09d4a93e-d5c8-4778-bdf2-711773d71c59",
      "api_id": "d5af91f6-a7ec-4015-b0a5-d25051158470",
      "application_id": "2f9f4d93-9193-4c49-a1a5-eddf0ff38abb",
      "created_at": 1736863661.511,
      "started_at": 1736863661.571,
      "finished_at": 1736863730.671,
      "elapsed": 69.1,
      "credential_id": "f634e655-012e-432e-92a8-a87e4a80d636",
      "request": {
        "action": "generate",
        "prompt": "Internal heat"
      },
      "trace_id": "0edc94c6-4938-4bff-bb16-20364c254e40",
      "user_id": "ad7afe47-cea9-4cda-980f-2ad8810e51cf",
      "response": {
        "success": true,
        "task_id": "09d4a93e-d5c8-4778-bdf2-711773d71c59",
        "trace_id": "0edc94c6-4938-4bff-bb16-20364c254e40",
        "data": [
          {
            "id": "24zdgea0s1rge0cmcmjbsfj2m8",
            "model": "minimax-t2v",
            "prompt": "Internal heat",
            "first_image_url": null,
            "video_url": "https://platform.cdn.acedata.cloud/czjl/6cTYBRBDVJIQANzG7GaPwPblbeIiFe4yUDcVoMkkXttqJCFUA/tmpm4ke45c5.output.mp4",
            "state": "succeeded"
          }
        ]
      }
    },
    {
      "_id": "67866dff550a4144a5867aa7",
      "id": "58cc618b-9639-4ee7-add2-d2fcf260d9a3",
      "api_id": "d5af91f6-a7ec-4015-b0a5-d25051158470",
      "application_id": "2f9f4d93-9193-4c49-a1a5-eddf0ff38abb",
      "created_at": 1736863231.588,
      "started_at": 1736863231.648,
      "finished_at": 1736863300.748,
      "elapsed": 69.1,
      "credential_id": "f634e655-012e-432e-92a8-a87e4a80d636",
      "request": {
        "action": "generate",
        "prompt": "Internal heat"
      },
      "trace_id": "0c1f9f13-0aef-4d9a-a9d2-1d27055ff190",
      "user_id": "ad7afe47-cea9-4cda-980f-2ad8810e51cf",
      "response": {
        "success": true,
        "task_id": "58cc618b-9639-4ee7-add2-d2fcf260d9a3",
        "trace_id": "0c1f9f13-0aef-4d9a-a9d2-1d27055ff190",
        "data": [
          {
            "id": "2a1tbgnjdxrg80cmcmes19s33r",
            "model": "minimax-t2v",
            "prompt": "Internal heat",
            "first_image_url": null,
            "video_url": "https://platform.cdn.acedata.cloud/czjl/tjU3QYKgU96IJFgpL0eMfBFhmy0qXz9Y05P2IBhShCYaDCFUA/tmp5uligw3a.output.mp4",
            "state": "succeeded"
          }
        ]
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

通过本文档，您已经了解了如何使用 Hailuo Tasks API 进行查询单个或批量视频任务的所有具体详情信息。希望本文档能帮助您更好地对接和使用该 API。如有任何问题，请随时联系我们的技术支持团队。
