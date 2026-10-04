# SeeDance Tasks API 的对接和使用

SeeDance Tasks API 的主要功能是通过输入 SeeDance Video Generation API 生成的任务ID来查询该任务的执行情况。


本文档将详细介绍 SeeDance Tasks API 的对接说明，帮助您轻松集成并充分利用该 API 的强大功能。通过 SeeDance Tasks API ，您可以轻松实现查询 SeeDance Video Generation API 的任务执行情况。

## 申请流程

要使用 SeeDance Video Generation API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[SeeDance Video Generation API →](https://platform.acedata.cloud/documents/seedance-videos)

## 请求示例
SeeDance Tasks API 可以用于查询 SeeDance Video Generation API 的结果。关于怎样使用 SeeDance Video Generation API，请参考文档 [SeeDance Video Generation API ](https://platform.acedata.cloud/documents/seedance-videos-integration)。

我们以 SeeDance Video Generation API 服务返回的任务ID一个为例，演示如何使用该 API。假设我们有一个任务ID：20068983-0cc9-4c6a-aeb6-9c6a3c668be0，接下来演示如何通过传入一个任务ID来。

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
curl -X POST 'https://api.acedata.cloud/seedance/tasks' \
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
    "_id": "69480c5cff2676299c7b351d",
    "id": "9462ca25-468b-45a5-9e75-6f516dedcc80",
    "api_id": "44e45d2b-8754-4a93-b793-c63271335f6f",
    "application_id": "1456a4bf-e2f4-4247-9b2d-fb49effc6eca",
    "created_at": 1766329436.091,
    "started_at": 1766329436.151,
    "finished_at": 1766329518.051,
    "elapsed": 81.9,
    "credential_id": "3e20b461-f750-48d3-a1f7-3aea48d15d77",
    "request": {
        "model": "doubao-seedance-1-0-pro-250528",
        "content": [
            {
                "type": "text",
                "text": "多个镜头。一名侦探进入一间光线昏暗的房间。他检查桌上的线索，手里拿起桌上的某个物品。镜头转向他正在思索。 --ratio 16:9"
            }
        ],
        "callback_url": "dummy"
    },
    "trace_id": "24b1b09c-5649-4290-98db-eab23e5efcac",
    "type": "videos",
    "user_id": "ad7afe47-cea9-4cda-980f-2ad8810e51cf",
    "response": {
        "success": true,
        "task_id": "9462ca25-468b-45a5-9e75-6f516dedcc80",
        "trace_id": "24b1b09c-5649-4290-98db-eab23e5efcac",
        "data": {
            "task_id": "cgt-20251221230356-sxgt7",
            "status": "succeeded",
            "video_url": "https://platform.cdn.acedata.cloud/seedance/d1c2e49e-d854-4a2e-b0c0-88e520f82e2e.mp4",
            "last_frame_url": null,
            "model": "doubao-seedance-1-0-pro-250528"
        }
    }
}
```

返回结果一共有多个字段，request 字段就是发起任务时的 request body，同时response 字段是任务完成后返回的response body。字段介绍如下。

- `id`，生成任务的 ID，用于唯一标识此次生成任务。
- `request`，查询任务中的请求信息。
- `response`，查询任务中的返回信息。
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

<p><img src="https://cdn.acedata.cloud/ycc4th.png" width="500" class="m-auto"></p>

### 代码示例

可以发现，在页面右侧已经自动生成了各种语言的代码，如图所示：

<p><img src="https://cdn.acedata.cloud/u6bt64.png" width="500" class="m-auto"></p>

部分代码示例如下：

#### CURL

```bash
curl -X POST 'https://api.acedata.cloud/seedance/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "ids": ["9462ca25-468b-45a5-9e75-6f516dedcc80","d9e576bd-ca14-4c6f-a541-f4734e941dbe"],
  "action": "retrieve_batch"
}'
```

### 响应示例

请求成功后，API 将返回此次所有批量任务的具体详情信息。例如：

```json
{
    "items": [
        {
            "_id": "69480c5cff2676299c7b351d",
            "id": "9462ca25-468b-45a5-9e75-6f516dedcc80",
            "api_id": "44e45d2b-8754-4a93-b793-c63271335f6f",
            "application_id": "1456a4bf-e2f4-4247-9b2d-fb49effc6eca",
            "created_at": 1766329436.091,
            "started_at": 1766329436.151,
            "finished_at": 1766329518.051,
            "elapsed": 81.9,
            "credential_id": "3e20b461-f750-48d3-a1f7-3aea48d15d77",
            "request": {
                "model": "doubao-seedance-1-0-pro-250528",
                "content": [
                    {
                        "type": "text",
                        "text": "多个镜头。一名侦探进入一间光线昏暗的房间。他检查桌上的线索，手里拿起桌上的某个物品。镜头转向他正在思索。 --ratio 16:9"
                    }
                ],
                "callback_url": "dummy"
            },
            "trace_id": "24b1b09c-5649-4290-98db-eab23e5efcac",
            "type": "videos",
            "user_id": "ad7afe47-cea9-4cda-980f-2ad8810e51cf",
            "response": {
                "success": true,
                "task_id": "9462ca25-468b-45a5-9e75-6f516dedcc80",
                "trace_id": "24b1b09c-5649-4290-98db-eab23e5efcac",
                "data": {
                    "task_id": "cgt-20251221230356-sxgt7",
                    "status": "succeeded",
                    "video_url": "https://platform.cdn.acedata.cloud/seedance/d1c2e49e-d854-4a2e-b0c0-88e520f82e2e.mp4",
                    "last_frame_url": null,
                    "model": "doubao-seedance-1-0-pro-250528"
                }
            }
        },
        {
            "_id": "69480e0dff2676299c7cb98b",
            "id": "d9e576bd-ca14-4c6f-a541-f4734e941dbe",
            "api_id": "44e45d2b-8754-4a93-b793-c63271335f6f",
            "application_id": "1456a4bf-e2f4-4247-9b2d-fb49effc6eca",
            "created_at": 1766329436.091,
            "started_at": 1766329436.151,
            "finished_at": 1766329518.051,
            "elapsed": 81.9,
            "credential_id": "3e20b461-f750-48d3-a1f7-3aea48d15d77",
            "request": {
                "model": "doubao-seedance-1-0-pro-250528",
                "content": [
                    {
                        "type": "text",
                        "text": "多个镜头。一名侦探进入一间光线昏暗的房间。他检查桌上的线索，手里拿起桌上的某个物品。镜头转向他正在思索。 --ratio 16:9"
                    }
                ],
                "callback_url": "dummy"
            },
            "trace_id": "e3da01aa-5026-4653-8d07-c68c4fcf466a",
            "type": "videos",
            "user_id": "ad7afe47-cea9-4cda-980f-2ad8810e51cf",
            "response": {
                "success": true,
                "task_id": "d9e576bd-ca14-4c6f-a541-f4734e941dbe",
                "trace_id": "e3da01aa-5026-4653-8d07-c68c4fcf466a",
                "data": {
                    "task_id": "cgt-20251221231109-cnkhp",
                    "status": "succeeded",
                    "video_url": "https://platform.cdn.acedata.cloud/seedance/eb99ba03-178c-4616-8d19-e625fee2e884.mp4",
                    "last_frame_url": null,
                    "model": "doubao-seedance-1-0-pro-250528"
                }
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

通过本文档，您已经了解了如何使用 SeeDance Tasks API 进行查询单个或批量任务的所有具体详情信息。希望本文档能帮助您更好地对接和使用该 API。如有任何问题，请随时联系我们的技术支持团队。
