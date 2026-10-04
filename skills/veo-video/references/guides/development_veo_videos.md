# Veo Videos Generation API 对接说明

本文将介绍一种 Veo Videos Generation API 对接说明，它是可以通过输入自定义参数来生成Veo官方的视频。

## 申请流程

要使用 Veo Videos Generation API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Veo Videos Generation API →](https://platform.acedata.cloud/documents/veo-videos)

## 基本使用

首先先了解下基本的使用方式，就是输入提示词 `prompt`、 生成行为 `action`、首尾帧参考图片数组 `image_urls` 以及模型 `model`，便可获得处理后的结果，首先需要简单地传递一个 `action` 字段，它的值为 `text2video`，它主要包含三种行为：文生视频（`text2video`）、图生视频（`image2video`）、获取1080p视频（`get1080p`），然后我们还需要输入模型 `model`，目前主要有 `veo31-fast`、`veo3`、`veo31`、`veo3-fast` 和 `veo31-fast-ingredients` 模型，具体的内容如下：

<p><img src="https://cdn.acedata.cloud/vv5pe8.png" width="500" class="m-auto"></p>

可以看到这里我们设置了 Request Headers，包括：

- `accept`：想要接收怎样格式的响应结果，这里填写为 `application/json`，即 JSON 格式。
- `authorization`：调用 API 的密钥，申请之后可以直接下拉选择。

另外设置了 Request Body，包括：

- `model`：生成视频的模型，主要有 `veo31-fast`、`veo3`、`veo31`、`veo3-fast` 和 `veo31-fast-ingredients` 模型。
- `action`：此次视频生成任务的行为，主要包含三种行为，分别为：文生视频（`text2video`）、图生视频（`image2video`）、获取1080p视频（`get1080p`）。
- `image_urls`：当选择图生视频行为 `image2video` 就必须需要上传的参考图片链接。`veo31-fast-ingredients` 最多 3 张（多图融合），其余模型最多 2 张（首尾帧模式）。
- `resolution`：选择生成的视频分辨率，其中veo31模型支持4k分辨率，其他模型不支持，所有模型均支持1080p以及gif分辨率，不传该值默认使用720p分辨率，主要分为：`1080p`、`gif`、`4k`。
- `prompt`：提示词。
- `callback_url`：需要回调结果的URL。
- `async`：可选，设为 `true` 时接口立即返回 `task_id`，无需提供 `callback_url`，随后通过对应的任务查询接口轮询获取结果。

### 📌 模型说明总结
| **模型名称**             | **支持模式**                                                                 | **图片输入规则**                                                                 |
|--------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| **veo3-fast**           | 文生视频（无图）<br>图生视频 模式（有图）                                      | **1 张** → 首帧模式<br>**2 张** → 首尾帧模式                                  |
| **veo31-fast**          | 文生视频（无图）<br>图生视频 模式（有图）                                      | **1 张** → 首帧模式<br>**2 张** → 首尾帧模式                                  |
| **veo31-fast-ingredients** | ❌ 文生视频（不支持）<br>✅ **强制多图融合**（必须传图）                 | **1-3 张** → 多图融合模式（最多 3 张）                                        |
| **veo3**                | 文生视频（无图）<br>图生视频 模式（有图）                                      | **1 张** → 首帧模式<br>**2 张** → 首尾帧模式                                  |
| **veo31**               | 文生视频（无图）<br>图生视频 模式（有图）                                      | **1 张** → 首帧模式<br>**2 张** → 首尾帧模式                                  |

---

### 🔑 关键规则说明
1. **通用逻辑**：
   - **无图片输入** → 自动触发文生视频模式。
   - **有图片输入** → 触发 图生视频 模式（具体行为由图片数量决定）。

2. **图生视频 模式类型**：
   - **首帧模式**（1 张图）：首帧固定为输入图片。
   - **首尾帧模式**（2 张图）：首帧和尾帧固定为输入图片。
   - **多图融合模式**（1-3 张图）：仅 `veo31-fast-ingredients` 支持，融合多图内容生成视频。

3. **模式分类**：
  - **Fast 模式**：`veo3-fast`、`veo31-fast`、`veo31-fast-ingredients`。
   - **Quality 模式**：`veo3`、`veo31`（生成质量更高）。

---

### ⚠️ 注意事项
- **唯一强制传图模型**：`veo31-fast-ingredients` 必须传入图片（1-3 张），否则无法运行。
- **图片数量限制**：
  - `veo31-fast-ingredients` 支持 **1-3 张**图片输入（多图融合模式）。
  - 其他模型最多支持 **2 张**图片输入（首尾帧模式）。


选择之后，可以发现右侧也生成了对应代码，如图所示：

<p><img src="https://cdn.acedata.cloud/pmwh4y.png" width="500" class="m-auto"></p>

点击「Try」按钮即可进行测试，如上图所示，这里我们就得到了如下结果：

```json
{
  "success": true,
  "task_id": "697ea2fc-58fd-48c8-8191-29041ff23c3c",
  "trace_id": "70e1cb12-c619-4292-a416-90191205996b",
  "data": [
    {
      "id": "24ac06a5-9cc7-448f-802e-0b4db19f6e96",
      "video_url": "https://cdn.acedata.cloud/assets/examples/veo/f5389ec0-2eb5-4212-b4a8-04b513b0129a-0b0c3113d691.mp4",
      "created_at": "2026-06-30T04:01:50.364Z",
      "complete_at": "2026-06-30T04:03:20.495Z",
      "state": "succeeded"
    }
  ]
}
```

返回结果一共有多个字段，介绍如下：

- `success`，此时视频生成任务的状态情况。
- `task_id`，此时视频生成任务ID。
- `data`，此时视频生成任务的结果。
  - `id`，此时视频生成任务的视频ID。
  - `video_url`，此时视频生成任务的视频链接。
  - `created_at`，此时视频生成任务的创建时间。
  - `complete_at`，此时视频生成任务的完成时间。
  - `state`，此时视频生成任务的状态。

可以看到我们得到了满意的视频信息，我们只需要根据结果中 `data` 的视频链接地址获取生成的Veo视频即可。

另外如果想生成对应的对接代码，可以直接复制生成，例如 CURL 的代码如下：

```shell
curl -X POST 'https://api.acedata.cloud/veo/videos' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "action": "text2video",
  "model": "veo31-fast",
  "prompt": "White ceramic coffee mug on glossy marble countertop with morning window light. Camera slowly rotates 360 degrees around the mug, pausing briefly at the handle."
}'
```
## 图生视频功能

如果想根据首尾帧图片进行生成视频的话，可以将参数 `action` 设置为 `image2video` ，并且输入首尾帧图片链接数组 `image_urls`。

接下来我们要必须填下一步需要扩展的提示词来自定义生成视频，就可以指定如下内容：

- `model`：生成视频的模型，主要有`veo31-fast`、`veo3`、`veo31`、`veo3-fast` 和 `veo31-fast-ingredients`。
- `image_urls`：当选择图生视频行为 `image2video` 就必须需要上传的参考图片链接。
- `prompt`：提示词。

填写样例如下：

<p><img src="https://cdn.acedata.cloud/8wvlqd.png" width="500" class="m-auto"></p>

填写完毕之后自动生成了代码如下：

<p><img src="https://cdn.acedata.cloud/tgzfxi.png" width="500" class="m-auto"></p>

对应的 Python 代码：

```python
import requests

url = "https://api.acedata.cloud/veo/videos"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "action": "image2video",
    "model": "veo31-fast",
    "prompt": "Let it dance",
    "image_urls": ["https://cdn.acedata.cloud/7p1jhy.png"]
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

点击运行，可以发现会得到一个结果，如下：

```json
{
  "success": true,
  "task_id": "98e309f3-35bc-438d-8cb3-4015fc864b87",
  "trace_id": "8bc68066-36de-41ef-ae5e-b7d61ff6aee8",
  "data": [
    {
      "id": "59f12222b1fa4fbe9331ff2400ad1583",
      "video_url": "https://platform.cdn.acedata.cloud/veo/98e309f3-35bc-438d-8cb3-4015fc864b87.mp4",
      "created_at": "2025-07-25 16:13:07",
      "complete_at": "2025-07-25 16:16:12",
      "state": "succeeded"
    }
  ]
}
```

可以看出，结果内容与上文的是一致的，这也就实现视频的图生视频功能。

## 获取1080p视频功能

如果想对已经生成的Veo视频获取1080p的话，可以将参数 `action` 设置为 `get1080p` ，并且输入需要获取1080p的视频的 ID，视频 ID 的获取是根据基本使用来获取，如下图所示：

<p><img src="https://cdn.acedata.cloud/hacabc.png" width="500" class="m-auto"></p>

这时候可以看到视频的 ID 为：

```json
"id": "59f12222b1fa4fbe9331ff2400ad1583"
```

> 注意，这里的视频中 `video_id` 是生成后视频的 ID，如果你不知道如何生成视频，可以参考上文的基本使用来生成视频。

接下来我们要必须填下一步需要扩展的提示词来自定义生成视频，就可以指定如下内容：

- `model`：生成视频的模型，主要有 `veo31-fast`、`veo3`、`veo31`、`veo3-fast` 和 `veo31-fast-ingredients`。
- `video_id`：参考的视频ID，用于获取1080p的视频。

填写样例如下：

<p><img src="https://cdn.acedata.cloud/k56fhn.png" width="500" class="m-auto"></p>

填写完毕之后自动生成了代码如下：

<p><img src="https://cdn.acedata.cloud/8gn4cr.png" width="500" class="m-auto"></p>

点击运行，可以发现会得到一个结果，如下：

```json
{
  "success": true,
  "task_id": "47a51cfe-2e24-4aba-93b3-546c2dc52984",
  "trace_id": "a8922eec-6f50-4f77-8104-00ded071d59d",
  "data": [
    {
      "id": "59f12222b1fa4fbe9331ff2400ad1583",
      "video_url": "https://platform.cdn.acedata.cloud/veo/47a51cfe-2e24-4aba-93b3-546c2dc52984.mp4",
      "created_at": "2025-07-25 16:13:07",
      "complete_at": "2025-07-25 16:16:12",
      "state": "succeeded"
    }
  ]
}
```

可以看出，结果内容与上文的是一致的，这也就实现视频的获取1080p视频功能。

## 指定视频尺寸生成

如果想指定生成自定义尺寸的Veo的视频，可以将参数 `aspect_ratio` 设置为想要的尺寸，接下来我们要必须填下一步需要扩展的提示词来自定义生成视频，就可以指定如下内容：

- `model`：生成视频的模型，主要有 `veo31-fast`、`veo3`、`veo31`、`veo3-fast` 和 `veo31-fast-ingredients`。
- `aspect_ratio`：视频的尺寸大小，目前支持：`16:9`、`16:9`、`3:4`、`4:3`、`1:1`，默认是`16:9`。
- `translation`：是否开启提示词的自动翻译，默认是 `false`。
填写样例如下：

<p><img src="https://cdn.acedata.cloud/xau4cm.png" width="500" class="m-auto"></p>

填写完毕之后自动生成了代码如下：

<p><img src="https://cdn.acedata.cloud/55r589.png" width="500" class="m-auto"></p>

点击运行，可以发现会得到一个结果，如下：

```json
{
  "success": true,
  "task_id": "d2b93290-ab0e-4d20-ae45-60c062a32687",
  "trace_id": "9834e64d-c8fe-43ae-8114-ee2b5f93d886",
  "data": [
    {
      "id": "fc667e7d3b8f44beaa61a3c339af0e50",
      "video_url": "https://platform.cdn.acedata.cloud/veo/d2b93290-ab0e-4d20-ae45-60c062a32687.mp4",
      "created_at": "2025-08-24 20:09:06",
      "complete_at": "2025-08-24 20:10:45",
      "state": "succeeded"
    }
  ]
}
```

可以看出，结果内容与上文的是一致的，这也就实现指定尺寸生成视频功能。

## 异步回调

由于 Veo Videos Generation API生成的时间相对较长，大约需要 1-2 分钟，如果 API 长时间无响应，HTTP 请求会一直保持连接，导致额外的系统资源消耗，所以本 API 也提供了异步回调的支持。

整体流程是：客户端发起请求的时候，额外指定一个 `callback_url` 字段，客户端发起 API 请求之后，API 会立马返回一个结果，包含一个 `task_id` 的字段信息，代表当前的任务 ID。当任务完成之后，生成视频的结果会通过 POST JSON 的形式发送到客户端指定的 `callback_url`，其中也包括了 `task_id` 字段，这样任务结果就可以通过 ID 关联起来了。

下面我们通过示例来了解下具体怎样操作。

首先，Webhook 回调是一个可以接收 HTTP 请求的服务，开发者应该替换为自己搭建的 HTTP 服务器的 URL。此处为了方便演示，使用一个公开的 Webhook 样例网站 https://webhook.site/，打开该网站即可得到一个 Webhook URL，如图所示：

![](https://cdn.acedata.cloud/tbcnai.png)

将此 URL 复制下来，就可以作为 Webhook 来使用，此处的样例为 `https://webhook.site/aed5cd28-f8aa-4dca-9480-8ec9b42137dc`。

接下来，我们可以设置字段 `callback_url` 为上述 Webhook URL，同时填入相应的参数，具体的内容如图所示：

<p><img src="https://cdn.acedata.cloud/rgivs2.png" width="500" class="m-auto"></p>

点击运行，可以发现会立即得到一个结果，如下：

```json
{
  "task_id": "1ebe4f2b-59ba-4385-a4ea-0ce8a3fe12ed"
}
```

稍等片刻，我们可以在 `https://webhook.site/aed5cd28-f8aa-4dca-9480-8ec9b42137dc` 上观察到生成视频的结果，如图所示：

![](https://cdn.acedata.cloud/238i32.png)

内容如下：

```json
{
  "success": true,
  "task_id": "1ebe4f2b-59ba-4385-a4ea-0ce8a3fe12ed",
  "trace_id": "d1d53c04-58c5-4c40-bb63-f00188540e56",
  "data": [
    {
      "id": "2f43ceed37944b4d836e1a1899dad0a1",
      "video_url": "https://platform.cdn.acedata.cloud/veo/1ebe4f2b-59ba-4385-a4ea-0ce8a3fe12ed.mp4",
      "created_at": "2025-07-25 17:19:20",
      "complete_at": "2025-07-25 17:21:45",
      "state": "succeeded"
    }
  ]
}
```

可以看到结果中有一个 `task_id` 字段，其他的字段都和上文类似，通过该字段即可实现任务的关联。


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

通过本文档，您已经了解了如何使用 Veo Videos Generation API 可通过输入提示词以及首帧参考图片来生成视频。希望本文档能帮助您更好地对接和使用该 API。如有任何问题，请随时联系我们的技术支持团队。
