# Gemini Videos Generation API 对接说明

本文将介绍 Gemini Videos Generation API 的对接说明，它可以通过输入文本提示词（以及可选的参考图片）来生成 Google Gemini（omni-flash）视频。

## 申请流程

要使用 Gemini Videos Generation API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Gemini Videos Generation API →](https://platform.acedata.cloud/documents/gemini-videos)

## 基本使用

首先了解下基本的使用方式，输入提示词 `prompt`、模型 `model` 以及宽高比 `aspect_ratio`，便可生成对应的视频。

可以看到这里我们设置了 Request Headers，包括：

- `accept`：想要接收怎样格式的响应结果，这里填写为 `application/json`，即 JSON 格式。
- `authorization`：调用 API 的密钥，申请之后可以直接下拉选择。

另外设置了 Request Body，包括：

- `prompt`：描述想要生成视频内容的文本提示词，**必填**。
- `model`：生成视频的模型，目前仅支持 `omni-flash`，默认即为 `omni-flash`。
- `aspect_ratio`：生成视频的宽高比，可选 `16:9`（横屏）或 `9:16`（竖屏），默认 `16:9`。
- `resolution`：可选的输出分辨率，可选 `720p` 或 `1080p`，默认 `720p`。
- `image_urls`：可选的参考图片链接数组，用于引导视频生成，留空项会被忽略。当使用 `video_urls` 进行视频编辑时，本参数必填（至少一张）。
- `video_urls`：可选的参考视频链接数组（最多 1 个），用于**视频编辑 / 视频参考**；提供时必须同时提供至少一张 `image_urls`。
- `callback_url`：异步回调地址，设置后 API 会立即返回 `task_id`，任务完成时将结果 POST 到该地址。
- `async`：可选，设为 `true` 时接口立即返回 `task_id`，无需提供 `callback_url`，随后通过对应的任务查询接口轮询获取结果。

点击「Try」按钮即可进行测试，得到的结果类似如下：

```json
{
  "success": true,
  "task_id": "9258c45f-bed9-4dde-81c2-a70a710a6904",
  "trace_id": "862d6aae-cec0-407f-9524-bc1be2291bcb",
  "data": [
    {
      "id": "dc4b7292-070c-49a8-8183-919bdf8ad59e",
      "video_url": "https://cdn.acedata.cloud/assets/examples/gemini/9258c45f-bed9-4dde-81c2-a70a710a6904-418c13e0605f.mp4",
      "state": "succeeded",
      "aspect_ratio": "16:9",
      "prompt": "A cinematic shot of a kitten chasing a butterfly in a sunlit garden"
    }
  ],
  "started_at": 1784112953.856,
  "finished_at": 1784113021.328,
  "elapsed": 67.472,
  "cost": {
    "amount": 1.932,
    "currency": "credit",
    "list_amount": 2.1
  }
}
```

返回结果一共有多个字段，介绍如下：

- `success`：本次视频生成请求是否成功。
- `task_id`：本次视频生成任务的 ID。
- `trace_id`：本次请求的跟踪 ID，用于排查问题。
- `data`：生成的视频结果列表。
  - `id`：生成视频的唯一标识。
  - `video_url`：生成视频的链接地址（`state` 为 `pending` 时为 `null`）。
  - `state`：视频生成任务的状态，可选 `pending` / `succeeded` / `failed`。
  - `aspect_ratio`：该视频的宽高比，与请求参数一致。
  - `prompt`：生成该视频所使用的提示词。

同步返回时，顶层还会附带 `started_at`、`finished_at`、`elapsed`（耗时，秒）以及 `cost`（本次扣费，单位 Credit）等字段。

我们只需要根据结果中 `data` 的 `video_url` 链接地址获取生成的视频即可。

对应的 CURL 代码如下：

```shell
curl -X POST 'https://api.acedata.cloud/gemini/videos' \
-H 'authorization: Bearer ${bearer_token}' \
-H 'accept: application/json' \
-H 'content-type: application/json' \
-d '{
  "prompt": "A cinematic shot of a kitten chasing a butterfly in a sunlit garden",
  "model": "omni-flash",
  "aspect_ratio": "16:9"
}'
```

对应的 Python 代码如下：

```python
import requests

url = "https://api.acedata.cloud/gemini/videos"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "prompt": "A cinematic shot of a kitten chasing a butterfly in a sunlit garden",
    "model": "omni-flash",
    "aspect_ratio": "16:9"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

## 图生视频

如果想基于参考图片生成视频，可以在 `image_urls` 中传入一个或多个图片链接，用于引导视频生成：

```json
{
  "prompt": "The woman slowly turns around and smiles at the camera, gentle breeze",
  "model": "omni-flash",
  "aspect_ratio": "9:16",
  "image_urls": [
    "https://cdn.acedata.cloud/assets/examples/nanobanana/e44bfceb-1458-4b4b-9d10-21024678f1a3-5ccb6e83b402.png"
  ]
}
```

## 视频编辑 / 参考视频（输入视频，生成视频）

支持直接「输入一段视频，生成一段新视频」：在 `video_urls` 中传入一个参考视频链接（最多 1 个），并**同时**在 `image_urls` 中提供至少一张参考图（上游硬性要求），再用 `prompt` 描述想要的编辑效果（改风格、换场景、增删元素等）。

下面是一个完整的真实示例——把一段阳光沙滩的视频改成大雪纷飞的冬日场景，同时保留沙滩、椰树和小船的布局。视频编辑耗时较长（本例约 6.5 分钟），因此用 `async: true` 异步提交：

```json
{
  "prompt": "Turn this sunny tropical beach into a snowy winter scene with heavy falling snow and overcast sky; keep the same beach, palm trees and boat layout.",
  "model": "omni-flash",
  "aspect_ratio": "9:16",
  "resolution": "720p",
  "image_urls": [
    "https://cdn.acedata.cloud/99289603bd.png"
  ],
  "video_urls": [
    "https://cdn.acedata.cloud/assets/examples/seedance/dd3dc063-3383-4f29-bedc-e771a096758c-044e05281a2a.mp4"
  ],
  "async": true
}
```

提交后接口立即返回 `task_id`：

```json
{
  "task_id": "cd68b4ee-de70-4c94-ac69-997a3fed0284"
}
```

之后用该 `task_id` 作为 `id` 轮询 [Gemini Tasks API](https://platform.acedata.cloud/documents/gemini-tasks)，任务完成后即可拿到生成的新视频（这是本示例的真实返回结果）：

```json
{
  "success": true,
  "task_id": "cd68b4ee-de70-4c94-ac69-997a3fed0284",
  "trace_id": "5b22104b-5a6d-4a4f-8063-69acae1dc1c6",
  "data": [
    {
      "id": "e125d316-3d26-4c65-9413-55baf6be46b8",
      "video_url": "https://cdn.acedata.cloud/assets/examples/sora/cd68b4ee-de70-4c94-ac69-997a3fed0284-c5603ef983da.mp4",
      "state": "succeeded",
      "aspect_ratio": "9:16",
      "prompt": "Turn this sunny tropical beach into a snowy winter scene with heavy falling snow and overcast sky; keep the same beach, palm trees and boat layout."
    }
  ],
  "started_at": 1784084482.914,
  "finished_at": 1784084877.09,
  "elapsed": 394.176,
  "cost": {
    "amount": 1.932,
    "currency": "credit",
    "list_amount": 2.1
  }
}
```

如需更高清的结果，可将 `resolution` 设为 `1080p`（其余参数不变）。

> 提示：示例中的输入 / 输出媒体链接均为真实生成结果。**平台生成的视频、图片链接有保存期限，过期后会失效**，请在拿到结果后及时下载保存到自己的存储。

> 注意：参考视频最多 1 个；且提供 `video_urls` 时必须提供至少一张 `image_urls`，否则会返回如下参数错误：

```json
{
  "success": false,
  "error": {
    "code": "bad_request",
    "message": "image_urls (at least one reference image) is required when video_urls is provided."
  }
}
```

## 异步回调

视频生成需要一定的处理时间。如果不希望保持长连接等待，可以传入 `callback_url`，此时 API 会立即返回 `task_id`，任务完成后会将最终结果 POST 到该地址：

```json
{
  "prompt": "A cinematic shot of a kitten chasing a butterfly in a sunlit garden",
  "model": "omni-flash",
  "aspect_ratio": "16:9",
  "callback_url": "https://your-domain.com/callback/gemini"
}
```

立即返回的结果如下：

```json
{
  "task_id": "04a043bd-6b23-4b4e-945c-ce48158c3eee"
}
```

## 查询任务结果

如果使用了异步回调或希望主动查询任务状态，可以通过 [Gemini Tasks API](https://platform.acedata.cloud/documents/gemini-tasks)（`POST https://api.acedata.cloud/gemini/tasks`）根据 `task_id` 查询任务的最新状态与结果。请求体中传入创建视频时返回的 `task_id` 作为 `id`：

```json
{
  "id": "04a043bd-6b23-4b4e-945c-ce48158c3eee"
}
```

任务完成后返回的结果类似如下，`response.data` 的结构与同步生成时一致（生成中时 `state` 为 `pending`、`video_url` 为 `null`）：

```json
{
  "id": "04a043bd-6b23-4b4e-945c-ce48158c3eee",
  "type": "videos",
  "request": {
    "model": "omni-flash",
    "prompt": "A time-lapse of clouds over snow mountains at sunrise",
    "aspect_ratio": "16:9",
    "async": true
  },
  "response": {
    "success": true,
    "task_id": "04a043bd-6b23-4b4e-945c-ce48158c3eee",
    "data": [
      {
        "id": "486ebd5a-6a4b-406c-84ae-33835de4fe19",
        "video_url": "https://cdn.acedata.cloud/assets/examples/gemini/04a043bd-6b23-4b4e-945c-ce48158c3eee-3a89912507c7.mp4",
        "state": "succeeded",
        "aspect_ratio": "16:9",
        "prompt": "A time-lapse of clouds over snow mountains at sunrise"
      }
    ],
    "elapsed": 96.716,
    "cost": {
      "amount": 1.932,
      "currency": "credit",
      "list_amount": 2.1
    }
  }
}
```

## 错误处理

当请求出现问题时，API 会返回对应的错误码与说明，常见的如下：

- `400`：请求参数有误，例如缺少 `prompt` 或 `aspect_ratio` 取值非法。
- `401`：鉴权失败，token 无效或与 API 不匹配。
- `403`：余额不足，或提示词命中内容审核被拒绝。
- `500`：服务器内部错误或上游生成失败。
