# SeeDream Tasks API 的对接和使用

SeeDream Tasks API 的主要功能是通过输入 SeeDream Images Generation API 生成的任务ID来查询该任务的执行情况。


本文档将详细介绍  SeeDream Tasks API  的对接说明，帮助您轻松集成并充分利用该 API 的强大功能。通过  SeeDream Tasks API ，您可以轻松实现查询  SeeDream Images Generation API 的任务执行情况。

## 申请流程

要使用 SeeDream Images Generation API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[SeeDream Images Generation API →](https://platform.acedata.cloud/documents/seedream-images)

## 请求示例
SeeDream Tasks API 可以用于查询 SeeDream Images Generation API 的结果。关于怎样使用 SeeDream Images  Generation API，请参考文档 [SeeDream Images Generation API ](https://platform.acedata.cloud/documents/seedream-images-integration)。

我们以 SeeDream Images Generation API 服务返回的任务ID一个为例，演示如何使用该 API。假设我们有一个任务ID：20068983-0cc9-4c6a-aeb6-9c6a3c668be0，接下来演示如何通过传入一个任务ID来。

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

<p><img src="https://cdn.acedata.cloud/yuyte9.png" width="500" class="m-auto"></p>

### 代码示例

可以发现，在页面右侧已经自动生成了各种语言的代码，如图所示：

<p><img src="https://cdn.acedata.cloud/b0wt0d.png" width="500" class="m-auto"></p>

部分代码示例如下：

#### CURL

```bash
curl -X POST 'https://api.acedata.cloud/seedream/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "id": "a6e0d456-189b-4c78-9232-2fe72166ab39",
  "action": "retrieve"
}'
```

### 响应示例

请求成功后，API 将返回此处任务的详情信息。例如：

```json
{
  "success": true,
  "task_id": "84d1544a-9043-4dde-a98b-e889dacd75f6",
  "trace_id": "176acf03-7ca7-4fc6-85db-e3724d4f59eb",
  "data": [
    {
      "prompt": "a white siamese cat",
      "size": "2048x2048",
      "image_url": "https://platform.cdn.acedata.cloud/seedream/6e5f9085-cc4a-4801-b77b-31550129ff19.jpg"
    }
  ]
}
```

返回结果一共有多个字段，介绍如下：
- `success`，此时视频生成任务的状态情况。
- `task_id`，此时视频生成任务 ID。
- `trace_id`，此时视频生成跟踪 ID。
- `data`，此时图像生成任务的结果列表。
  - `image_url`，此时图片生成任务的链接。
  - `prompt`，提示词。
  - `size`: 生成图的像素

## 批量查询操作

这是是针对多个任务ID来进行查询任务详情，与上面不同的是需要将action选中为retrieve_batch

**Request Body** 包括：

- `ids`：上传的任务ID数组。
- `action`：对任务的操作方式。

设置如下图所示：

<p><img src="https://cdn.acedata.cloud/ycc4th.png" width="500" class="m-auto"></p>

### 代码示例

部分代码示例如下：

#### CURL

```bash
curl -X POST 'https://api.acedata.cloud/seedance/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "ids": ["84d1544a-9043-4dde-a98b-e889dacd75f6","84d1544a-9043-4dde-a98b-e889dacd75f6"],
  "action": "retrieve_batch"
}'
```

### 响应示例

请求成功后，API 将返回此次所有批量任务的具体详情信息。例如：

```json
{
  "items": [
    {
      "_id": "69498b9bff2676299c5cb7a6",
      "id": "84d1544a-9043-4dde-a98b-e889dacd75f6",
      "api_id": "86ad30f3-0bc8-4b9b-b019-b9fa5b05672e",
      "application_id": "11e25072-de6d-4bd6-81e7-77ee0055499a",
      "created_at": 1766427547.107,
      "started_at": 1766427547.167,
      "finished_at": 1766427560.667,
      "elapsed": 13.5,
      "credential_id": "50892af9-597f-426e-a455-bc1739de95b0",
      "request": {
        "action": "generate",
        "model": "doubao-seedream-4-0-250828",
        "prompt": "a white siamese cat"
      },
      "trace_id": "176acf03-7ca7-4fc6-85db-e3724d4f59eb",
      "type": "images",
      "user_id": "b60a9491-1eba-4ab8-a93f-12c0fd81dab4",
      "response": {
        "success": true,
        "task_id": "84d1544a-9043-4dde-a98b-e889dacd75f6",
        "trace_id": "176acf03-7ca7-4fc6-85db-e3724d4f59eb",
        "data": [
          {
            "prompt": "a white siamese cat",
            "size": "2048x2048",
            "image_url": "https://platform.cdn.acedata.cloud/seedream/6e5f9085-cc4a-4801-b77b-31550129ff19.jpg"
          }
        ]
      }
    },
    {
      "_id": "69498b9bff2676299c5cb7a6",
      "id": "84d1544a-9043-4dde-a98b-e889dacd75f6",
      "api_id": "86ad30f3-0bc8-4b9b-b019-b9fa5b05672e",
      "application_id": "11e25072-de6d-4bd6-81e7-77ee0055499a",
      "created_at": 1766427547.107,
      "started_at": 1766427547.167,
      "finished_at": 1766427560.667,
      "elapsed": 13.5,
      "credential_id": "50892af9-597f-426e-a455-bc1739de95b0",
      "request": {
        "action": "generate",
        "model": "doubao-seedream-4-0-250828",
        "prompt": "a white siamese cat"
      },
      "trace_id": "176acf03-7ca7-4fc6-85db-e3724d4f59eb",
      "type": "images",
      "user_id": "b60a9491-1eba-4ab8-a93f-12c0fd81dab4",
      "response": {
        "success": true,
        "task_id": "84d1544a-9043-4dde-a98b-e889dacd75f6",
        "trace_id": "176acf03-7ca7-4fc6-85db-e3724d4f59eb",
        "data": [
          {
            "prompt": "a white siamese cat",
            "size": "2048x2048",
            "image_url": "https://platform.cdn.acedata.cloud/seedream/6e5f9085-cc4a-4801-b77b-31550129ff19.jpg"
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

批量结果里每个任务对象还带有以下计时字段。

- `created_at`，任务创建时间，Unix 时间戳（秒，浮点）。
- `started_at`，任务开始执行时间，Unix 时间戳（秒，浮点）。
- `finished_at`，任务完成时间，Unix 时间戳（秒，浮点）。任务未完成时不返回该字段。
- `elapsed`，任务执行耗时，单位为秒（浮点，保留 3 位小数）。任务未完成时不返回该字段。

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

通过本文档，您已经了解了如何使用 SeeDream Tasks API 进行查询单个或批量任务的所有具体详情信息。希望本文档能帮助您更好地对接和使用该 API。如有任何问题，请随时联系我们的技术支持团队。
