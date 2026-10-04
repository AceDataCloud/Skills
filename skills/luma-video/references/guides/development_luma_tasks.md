# Luma Tasks API 的对接和使用

Luma Tasks API 的主要功能是通过输入 Luma Videos Generation API 生成的任务ID来查询该任务的执行情况。


本文档将详细介绍  Luma Tasks API  的对接说明，帮助您轻松集成并充分利用该 API 的强大功能。通过  Luma Tasks API ，您可以轻松实现查询 Luma Videos Generation API 的任务执行情况。

## 申请流程

要使用 Luma Videos Generation API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Luma Videos Generation API →](https://platform.acedata.cloud/documents/luma-videos)

## 请求示例
Luma Tasks API 可以用于查询 Luma Videos Generation API 的结果。关于怎样使用 Luma Videos Generation API，请参考文档 [Luma Videos Generation API](https://platform.acedata.cloud/documents/luma-videos-integration)。

我们以 Luma Videos Generation API 服务返回的任务ID一个为例，演示如何使用该 API。假设我们有一个任务ID：50fc6182-fa86-4c7d-ac12-2fa27ec2f151，接下来演示如何通过传入一个任务ID来。

### 任务示例图

<p><img src="https://cdn.acedata.cloud/frcrux.png" width="500" class="m-auto"></p>

### 设置请求头和请求体

**Request Headers** 包括：

- `accept`：指定接收 JSON 格式的响应结果，这里填写为 `application/json`。
- `authorization`：调用 API 的密钥，申请之后可以直接下拉选择。

**Request Body** 包括：

- `id`：上传的任务ID。
- `action`：对任务的操作方式。

设置如下图所示：

<p><img src="https://cdn.acedata.cloud/g6ev5b.png" width="500" class="m-auto"></p>

### 代码示例

可以发现，在页面右侧已经自动生成了各种语言的代码，如图所示：

<p><img src="https://cdn.acedata.cloud/i4fxqf.png" width="500" class="m-auto"></p>

部分代码示例如下：

#### CURL

```bash
curl -X POST 'https://api.acedata.cloud/luma/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "id": "50fc6182-fa86-4c7d-ac12-2fa27ec2f151",
  "action": "retrieve"
}'
```

#### Python

```python
import requests

url = "https://api.acedata.cloud/luma/tasks"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "id": "50fc6182-fa86-4c7d-ac12-2fa27ec2f151",
    "action": "retrieve"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

### 响应示例

请求成功后，API 将返回此处视频任务的详情信息。例如：

```json
{
  "_id": "66d297a3550a4144a5a5db42",
  "id": "50fc6182-fa86-4c7d-ac12-2fa27ec2f151",
  "api_id": "94fc9028-5a9f-4875-aae4-38463bd30ac5",
  "application_id": "06484a45-9d04-498a-98a7-67086dee8166",
  "created_at": 1725077411.961,
  "started_at": 1725077412.021,
  "finished_at": 1725077566.241,
  "elapsed": 154.22,
  "credential_id": "e6a879e5-a7c0-4f7b-9d6f-f9a837421a50",
  "request": {
    "action": "generate",
    "prompt": "Astronauts shuttle from space to volcano"
  },
  "trace_id": "0b7c1c1a-045c-4145-a434-609cba88f0a9",
  "user_id": "ad7afe47-cea9-4cda-980f-2ad8810e51cf",
  "response": {
    "success": true,
    "task_id": "50fc6182-fa86-4c7d-ac12-2fa27ec2f151",
    "video_id": "4b088fc8-2bbc-4706-80a6-a0fb118adc1a",
    "prompt": "Astronauts shuttle from space to volcano",
    "video_url": "https://platform.cdn.acedata.cloud/luma/50fc6182-fa86-4c7d-ac12-2fa27ec2f151.mp4",
    "video_height": 752,
    "video_width": 1360,
    "state": "completed",
    "thumbnail_url": "https://platform.cdn.acedata.cloud/luma/50fc6182-fa86-4c7d-ac12-2fa27ec2f151.jpg",
    "thumbnail_width": 1360,
    "thumbnail_height": 752
  }
}
```

返回结果一共有多个字段，request 字段就是发起任务时的 request body，同时response 字段是任务完成后返回的response body，其结果和 Luma Videos Generation API 的请求和返回一致。字段介绍如下。

- `id`，生成此视频任务的 ID，用于唯一标识此次视频生成任务。
- `video_id`，此处查询的视频任务中视频的唯一标识，在下次需要对视频进行扩展操作时需要传此参数。
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

<p><img src="https://cdn.acedata.cloud/mpcf1m.png" width="500" class="m-auto"></p>

### 代码示例

可以发现，在页面右侧已经自动生成了各种语言的代码，如图所示：

<p><img src="https://cdn.acedata.cloud/zs6y35.png" width="500" class="m-auto"></p>

部分代码示例如下：

#### CURL

```bash
curl -X POST 'https://api.acedata.cloud/luma/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "ids": ["50fc6182-fa86-4c7d-ac12-2fa27ec2f151","76a05f61-68ad-4c1a-838f-a00cd08cf65b"],
  "action": "retrieve_batch"
}'
```

#### Python

```python
import requests

url = "https://api.acedata.cloud/luma/tasks"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "ids": ["50fc6182-fa86-4c7d-ac12-2fa27ec2f151","76a05f61-68ad-4c1a-838f-a00cd08cf65b"],
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
      "_id": "66d297a3550a4144a5a5db42",
      "id": "50fc6182-fa86-4c7d-ac12-2fa27ec2f151",
      "api_id": "94fc9028-5a9f-4875-aae4-38463bd30ac5",
      "application_id": "06484a45-9d04-498a-98a7-67086dee8166",
      "created_at": 1725077411.961,
      "started_at": 1725077412.021,
      "finished_at": 1725077566.241,
      "elapsed": 154.22,
      "credential_id": "e6a879e5-a7c0-4f7b-9d6f-f9a837421a50",
      "request": {
        "action": "generate",
        "prompt": "Astronauts shuttle from space to volcano"
      },
      "trace_id": "0b7c1c1a-045c-4145-a434-609cba88f0a9",
      "user_id": "ad7afe47-cea9-4cda-980f-2ad8810e51cf",
      "response": {
        "success": true,
        "task_id": "50fc6182-fa86-4c7d-ac12-2fa27ec2f151",
        "video_id": "4b088fc8-2bbc-4706-80a6-a0fb118adc1a",
        "prompt": "Astronauts shuttle from space to volcano",
        "video_url": "https://platform.cdn.acedata.cloud/luma/50fc6182-fa86-4c7d-ac12-2fa27ec2f151.mp4",
        "video_height": 752,
        "video_width": 1360,
        "state": "completed",
        "thumbnail_url": "https://platform.cdn.acedata.cloud/luma/50fc6182-fa86-4c7d-ac12-2fa27ec2f151.jpg",
        "thumbnail_width": 1360,
        "thumbnail_height": 752
      }
    },
    {
      "_id": "66d29ed3550a4144a5a6c089",
      "id": "76a05f61-68ad-4c1a-838f-a00cd08cf65b",
      "api_id": "94fc9028-5a9f-4875-aae4-38463bd30ac5",
      "application_id": "06484a45-9d04-498a-98a7-67086dee8166",
      "created_at": 1725079250.921,
      "started_at": 1725079250.981,
      "finished_at": 1725079406.71,
      "elapsed": 155.729,
      "credential_id": "e6a879e5-a7c0-4f7b-9d6f-f9a837421a50",
      "request": {
        "action": "generate",
        "prompt": "la la la"
      },
      "trace_id": "338f1616-741d-40b6-8d62-c025434024c6",
      "user_id": "ad7afe47-cea9-4cda-980f-2ad8810e51cf",
      "response": {
        "success": true,
        "task_id": "76a05f61-68ad-4c1a-838f-a00cd08cf65b",
        "video_id": "5a638d6a-7481-4c5e-8843-36c9d1b5bcd5",
        "prompt": "la la la",
        "video_url": "https://platform.cdn.acedata.cloud/luma/76a05f61-68ad-4c1a-838f-a00cd08cf65b.mp4",
        "video_height": 752,
        "video_width": 1360,
        "state": "completed",
        "thumbnail_url": "https://platform.cdn.acedata.cloud/luma/76a05f61-68ad-4c1a-838f-a00cd08cf65b.jpg",
        "thumbnail_width": 1360,
        "thumbnail_height": 752
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

通过本文档，您已经了解了如何使用 Luma Tasks API 进行查询单个或批量视频任务的所有具体详情信息。希望本文档能帮助您更好地对接和使用该 API。如有任何问题，请随时联系我们的技术支持团队。
