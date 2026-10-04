# Grok Videos Generation API 对接说明

本文将介绍 Grok Videos Generation API 的对接说明，它可以通过输入文本提示词、输入图片以及可选的参考图片来生成 Grok Imagine（xAI）视频。

## 申请流程

要使用 Grok Videos Generation API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Grok Videos Generation API →](https://platform.acedata.cloud/documents/grok-videos)

## 模型说明

本 API 通过模型名的后缀选择上游端点：`:reverse` 走快速/标准端点（更便宜），`:official` 走官方端点（画质更高，按输出秒数计费）。共支持四个模型：

- `grok-imagine-video-1.5-fast:reverse`（默认）：支持文生视频（仅传 `prompt`）和图生视频（传 `image_url`），时长 6–30 秒，按时长分档计费，最便宜。
- `grok-imagine-video:reverse`：支持文生与图生视频，时长 1–15 秒，按输出秒数计费。
- `grok-imagine-video:official`：官方端点，支持文生与图生视频，时长 1–15 秒，按输出秒数计费，画质更高。
- `grok-imagine-video-1.5:official`：官方端点，**仅支持图生视频**，**必须**传入 `image_url`，时长 1–15 秒，支持最高 `1080p`，按输出秒数计费。

## 基本使用

首先了解下基本的使用方式，输入提示词 `prompt`、模型 `model` 等参数，便可生成对应的视频。

可以看到这里我们设置了 Request Headers，包括：

- `accept`：想要接收怎样格式的响应结果，这里填写为 `application/json`，即 JSON 格式。
- `authorization`：调用 API 的密钥，申请之后可以直接下拉选择。

另外设置了 Request Body，包括：

- `prompt`：描述想要生成视频内容的文本提示词。做文生视频时**必填**；传入 `image_url` 时可选。
- `model`：生成视频的模型，可选 `grok-imagine-video-1.5-fast:reverse`（默认）、`grok-imagine-video:reverse`、`grok-imagine-video:official` 或 `grok-imagine-video-1.5:official`。
- `image_url`：图生视频的输入图片链接。当 `model` 为 `grok-imagine-video-1.5:official` 时**必填**。
- `reference_image_urls`：可选的参考图片链接数组，用于引导视频的风格或内容。
- `aspect_ratio`：生成视频的宽高比，可选 `1:1` / `16:9` / `9:16` / `4:3` / `3:4` / `3:2` / `2:3`。
- `resolution`：输出分辨率，可选 `480p`（默认）、`720p` 或 `1080p`。
- `duration`：生成视频的时长（秒）。`grok-imagine-video-1.5-fast:reverse` 取值范围 6–30，其余模型取值范围 1–15，默认 6。推荐使用 6 秒或 10 秒，这两个标准时长相对稳定。
- `callback_url`：异步回调地址，设置后 API 会立即返回 `task_id`，任务完成时将结果 POST 到该地址。
- `async`：可选，设为 `true` 时接口立即返回 `task_id`，无需提供 `callback_url`，随后通过对应的任务查询接口轮询获取结果。

点击「Try」按钮即可进行测试，得到的结果类似如下：

```json
{
  "success": true,
  "task_id": "b8976e18-32dc-4718-9ed8-1ea090fcb6ea",
  "trace_id": "fb751e1e-4705-49ea-9fd4-5024b7865ea2",
  "data": [
    {
      "id": "grok-imagine-video-1.5-fast:reverse:41eb9a5f-3b2d-4d1e-9f5a-6c2f1a0b9e77",
      "video_url": "https://cdn.acedata.cloud/c8cbf53aa0.mp4",
      "state": "succeeded"
    }
  ]
}
```

返回结果一共有多个字段，介绍如下：

- `success`：本次视频生成请求是否成功。
- `task_id`：本次视频生成任务的 ID。
- `trace_id`：本次请求的跟踪 ID，用于排查问题。
- `data`：生成的视频结果列表。
  - `id`：生成视频的唯一标识。
  - `video_url`：生成视频的链接地址。
  - `state`：视频生成任务的状态，可选 `pending` / `succeeded` / `failed`。

我们只需要根据结果中 `data` 的 `video_url` 链接地址获取生成的视频即可。

对应的 CURL 代码如下：

```shell
curl -X POST 'https://api.acedata.cloud/grok/videos' \
-H 'authorization: Bearer ${bearer_token}' \
-H 'accept: application/json' \
-H 'content-type: application/json' \
-d '{
  "prompt": "A cinematic shot of a kitten chasing a butterfly in a sunlit garden",
  "model": "grok-imagine-video-1.5-fast:reverse",
  "resolution": "480p",
  "duration": 6
}'
```

对应的 Python 代码如下：

```python
import requests

url = "https://api.acedata.cloud/grok/videos"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "prompt": "A cinematic shot of a kitten chasing a butterfly in a sunlit garden",
    "model": "grok-imagine-video-1.5-fast:reverse",
    "resolution": "480p",
    "duration": 6
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

## 图生视频

如果想基于一张输入图片生成视频，可以传入 `image_url`。使用 `grok-imagine-video-1.5:official` 时必须提供该字段：

```json
{
  "prompt": "The character slowly turns around and smiles at the camera",
  "model": "grok-imagine-video-1.5:official",
  "image_url": "https://cdn.acedata.cloud/5hmkdg.jpg",
  "resolution": "720p",
  "duration": 6
}
```

## 参考图引导

如果想用一张或多张参考图引导生成视频的风格或内容，可以在 `reference_image_urls` 中传入图片链接数组：

```json
{
  "prompt": "A character dancing in the same art style",
  "model": "grok-imagine-video-1.5-fast:reverse",
  "reference_image_urls": [
    "https://cdn.acedata.cloud/vunnjf.png"
  ]
}
```

## 异步回调

视频生成需要一定的处理时间。如果不希望保持长连接等待，可以传入 `callback_url`，此时 API 会立即返回 `task_id`，任务完成后会将最终结果 POST 到该地址：

```json
{
  "prompt": "A cinematic shot of a kitten chasing a butterfly in a sunlit garden",
  "model": "grok-imagine-video-1.5-fast:reverse",
  "duration": 6,
  "callback_url": "https://your-domain.com/callback/grok"
}
```

立即返回的结果如下：

```json
{
  "task_id": "b8976e18-32dc-4718-9ed8-1ea090fcb6ea"
}
```

## 查询任务结果

如果使用了异步回调或希望主动查询任务状态，可以通过 [Grok Tasks API](https://platform.acedata.cloud/documents/grok-tasks)（`POST https://api.acedata.cloud/grok/tasks`）根据 `task_id` 查询任务的最新状态与结果。

## 计费说明

本服务的计费方式由 `model` 决定：

- `grok-imagine-video-1.5-fast:reverse`：按时长分档计费，与分辨率无关——`6–10` 秒、`11–20` 秒、`21–30` 秒分别对应不同档位价格。
- `grok-imagine-video:reverse`：按「输出秒数」计费，总价 = 单价 × `duration`。
- `grok-imagine-video:official` 与 `grok-imagine-video-1.5:official`：官方端点，按「输出秒数」计费，分辨率越高单价越高；官方模型即使内容审核失败也会计费。

具体单价以定价页为准。失败的请求不计费，也不占用免费额度。

## 错误处理

当请求出现问题时，API 会返回对应的错误码与说明，常见的如下：

- `400`：请求参数有误，例如文生视频缺少 `prompt`，或 `grok-imagine-video-1.5:official` 缺少 `image_url`，或 `duration` 超出范围（`grok-imagine-video-1.5-fast:reverse` 为 6–30，其余模型为 1–15）。
- `401`：鉴权失败，token 无效或与 API 不匹配。
- `403`：余额不足，或提示词命中内容审核被拒绝。
- `429`：请求过于频繁，请稍后重试。
- `500`：视频生成失败或服务异常。
