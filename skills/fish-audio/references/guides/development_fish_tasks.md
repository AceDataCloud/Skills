# Fish Tasks API 的对接和使用

Fish Tasks API 的主要功能是通过输入 Fish Audios Generation API 生成的任务ID来查询该任务的执行情况。


本文档将详细介绍  Fish Tasks API  的对接说明，帮助您轻松集成并充分利用该 API 的强大功能。通过  Fish Tasks API ，您可以轻松实现查询  Fish Audios Generation API 的任务执行情况。

## 申请流程

要使用 Fish Audios Generation API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Fish Audios Generation API →](https://platform.acedata.cloud/documents/fish-tts)

## 请求示例
Fish Tasks API 可以用于查询 Fish Audios Generation API 的结果。关于怎样使用 Fish Audios Generation API，请参考文档 [Fish Videos Generation API ](https://platform.acedata.cloud/documents/fish-tts-integration)。

我们以 Fish Audios Generation API 服务返回的任务ID一个为例，演示如何使用该 API。假设我们有一个任务ID：2725a2d3-f87e-4905-9c53-9988d5a7b2f5，接下来演示如何通过传入一个任务ID来。

### 任务示例图

<p><img src="https://cdn.acedata.cloud/jxvue8.png" width="500" class="m-auto"></p>

### 设置请求头和请求体

**Request Headers** 包括：

- `accept`：指定接收 JSON 格式的响应结果，这里填写为 `application/json`。
- `authorization`：调用 API 的密钥，申请之后可以直接下拉选择。

**Request Body** 包括：

- `id`：上传的任务ID。
- `action`：对任务的操作方式。

设置如下图所示：

<p><img src="https://cdn.acedata.cloud/xc5ejq.png" width="500" class="m-auto"></p>

### 代码示例

可以发现，在页面右侧已经自动生成了各种语言的代码，如图所示：

<p><img src="https://cdn.acedata.cloud/851zv2.png" width="500" class="m-auto"></p>

部分代码示例如下：

#### CURL

```bash
curl -X POST 'https://api.acedata.cloud/fish/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "id": "2725a2d3-f87e-4905-9c53-9988d5a7b2f5",
  "action": "retrieve"
}'
```


### 响应示例

请求成功后，API 将返回此处任务的详情信息。例如：

```json
{
  "_id": "68cfad98550a4144a5476a92",
  "id": "2725a2d3-f87e-4905-9c53-9988d5a7b2f5",
  "api_id": "8e6f8083-4683-45fe-a993-3e1d993fc999",
  "application_id": "3559d836-2505-46be-96ea-ea72bcb7c080",
  "created_at": 1758440856.34,
  "started_at": 1758440856.4,
  "finished_at": 1758440869.2,
  "elapsed": 12.8,
  "credential_id": "881ad87d-8ba7-40b7-ac45-d19e41ae6e3a",
  "request": {
    "action": "speech",
    "prompt": "a white siamese cat",
    "model": "fish-tts",
    "voice_id": "d7900c21663f485ab63ebdb7e5905036",
    "callback_url": "https://webhook.site/4815f79f-a40f-4078-ac85-1cc126b6bb34"
  },
  "trace_id": "e2d308bc-4df8-4c69-9369-a60f3c54f2b3",
  "type": "audios",
  "user_id": "ad7afe47-cea9-4cda-980f-2ad8810e51cf",
  "response": {
    "success": true,
    "task_id": "2725a2d3-f87e-4905-9c53-9988d5a7b2f5",
    "trace_id": "e2d308bc-4df8-4c69-9369-a60f3c54f2b3",
    "data": [
      {
        "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3"
      }
    ]
  }
}
```

返回结果一共有多个字段，request 字段就是发起任务时的 request body，同时response 字段是任务完成后返回的response body。字段介绍如下。

- `id`，生成此任务的 ID，用于唯一标识此次生成任务。
- `request`，查询任务中的请求信息。
- `response`，查询任务中的返回信息；最终成功时其中的 `cost.amount` 是该次合成实际扣除的 Credits。
- `created_at`，任务创建时间，Unix 时间戳（秒，浮点）。
- `started_at`，任务开始执行时间，Unix 时间戳（秒，浮点）。
- `finished_at`，任务完成时间，Unix 时间戳（秒，浮点）。任务未完成时不返回该字段。
- `elapsed`，任务执行耗时，单位为秒（浮点，保留 3 位小数）。任务未完成时不返回该字段。

## 批量查询操作

这是是针对多个任务ID来进行查询任务详情，与上面不同的是需要将action选中为retrieve_batch

**Request Body** 包括：

- `ids`：上传的任务ID数组。
- `action`：对任务的操作方式。

设置如下图所示：

<p><img src="https://cdn.acedata.cloud/64lid9.png" width="500" class="m-auto"></p>

### 代码示例

可以发现，在页面右侧已经自动生成了各种语言的代码，如图所示：

<p><img src="https://cdn.acedata.cloud/ezkzmw.png" width="500" class="m-auto"></p>

部分代码示例如下：

#### CURL

```bash
curl -X POST 'https://api.acedata.cloud/fish/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "ids": ["2725a2d3-f87e-4905-9c53-9988d5a7b2f5","2725a2d3-f87e-4905-9c53-9988d5a7b2f5"],
  "action": "retrieve_batch"
}'
```

### 响应示例

请求成功后，API 将返回此次所有批量任务的具体详情信息。例如：

```json
{
  "items": [
    {
      "_id": "68cfad98550a4144a5476a92",
      "id": "2725a2d3-f87e-4905-9c53-9988d5a7b2f5",
      "api_id": "8e6f8083-4683-45fe-a993-3e1d993fc999",
      "application_id": "3559d836-2505-46be-96ea-ea72bcb7c080",
      "created_at": 1758440856.34,
      "started_at": 1758440856.4,
      "finished_at": 1758440869.2,
      "elapsed": 12.8,
      "credential_id": "881ad87d-8ba7-40b7-ac45-d19e41ae6e3a",
      "request": {
        "action": "speech",
        "prompt": "a white siamese cat",
        "model": "fish-tts",
        "voice_id": "d7900c21663f485ab63ebdb7e5905036",
        "callback_url": "https://webhook.site/4815f79f-a40f-4078-ac85-1cc126b6bb34"
      },
      "trace_id": "e2d308bc-4df8-4c69-9369-a60f3c54f2b3",
      "type": "audios",
      "user_id": "ad7afe47-cea9-4cda-980f-2ad8810e51cf",
      "response": {
        "success": true,
        "task_id": "2725a2d3-f87e-4905-9c53-9988d5a7b2f5",
        "trace_id": "e2d308bc-4df8-4c69-9369-a60f3c54f2b3",
        "data": [
          {
            "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3"
          }
        ]
      }
    },
    {
      "_id": "68cfad98550a4144a5476a92",
      "id": "2725a2d3-f87e-4905-9c53-9988d5a7b2f5",
      "api_id": "8e6f8083-4683-45fe-a993-3e1d993fc999",
      "application_id": "3559d836-2505-46be-96ea-ea72bcb7c080",
      "created_at": 1758440856.34,
      "started_at": 1758440856.4,
      "finished_at": 1758440869.2,
      "elapsed": 12.8,
      "credential_id": "881ad87d-8ba7-40b7-ac45-d19e41ae6e3a",
      "request": {
        "action": "speech",
        "prompt": "a white siamese cat",
        "model": "fish-tts",
        "voice_id": "d7900c21663f485ab63ebdb7e5905036",
        "callback_url": "https://webhook.site/4815f79f-a40f-4078-ac85-1cc126b6bb34"
      },
      "trace_id": "e2d308bc-4df8-4c69-9369-a60f3c54f2b3",
      "type": "audios",
      "user_id": "ad7afe47-cea9-4cda-980f-2ad8810e51cf",
      "response": {
        "success": true,
        "task_id": "2725a2d3-f87e-4905-9c53-9988d5a7b2f5",
        "trace_id": "e2d308bc-4df8-4c69-9369-a60f3c54f2b3",
        "data": [
          {
            "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3"
          }
        ]
      }
    }
  ],
  "count": 2
}
```

返回结果一共有多个字段，其中items是包含了批量任务的具体详情信息，每个任务的具体信息与上文的字段一样，字段信息如下。

- `items`，批量任务的所有具体详情信息。它是一个数组，每个数组的元素和上文查询单个任务的返回结果格式是一样的。
- `count`，此处批量查询任务的个数。

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

通过本文档，您已经了解了如何使用 Fish Tasks API 进行查询单个或批量任务的所有具体详情信息。希望本文档能帮助您更好地对接和使用该 API。如有任何问题，请随时联系我们的技术支持团队。
