# Kling Motion Generation API 对接说明

本文将介绍一种 Kling Motion Generation API 对接说明，它是可以通过输入自定义参数来生成Kling官方的视频。

## 申请流程

要使用 Kling Motion Generation API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Kling Motion Generation API →](https://platform.acedata.cloud/documents/kling-motion)

## 基本使用

首先先了解下基本的使用方式，就是输入提示词 `prompt`、参考图片 `image_url` 以及参考视频链接 `video_url`，便可获得处理后的结果，然后我们还需要输入模型 `mode`，目前主要有 `std`, `pro` 模型，具体的内容如下：

<p><img src="https://cdn.acedata.cloud/5qlpjt.png" width="500" class="m-auto"></p>

可以看到这里我们设置了 Request Headers，包括：

- `accept`：想要接收怎样格式的响应结果，这里填写为 `application/json`，即 JSON 格式。
- `authorization`：调用 API 的密钥，申请之后可以直接下拉选择。

另外设置了 Request Body，包括：

- `image_url`：人物外观参考图 URL。支持 JPG/JPEG/PNG，文件 ≤50MB，宽和高均 ≥300px，宽高比 1:2.5～2.5:1；人物应清晰显示上半身或全身及头部。
- `video_url`：动作参考视频 URL。支持 MP4/MOV，文件 ≤100MB，宽和高各 340–3850px，至少 3 秒；`character_orientation=image` 时最长 10 秒，`character_orientation=video` 时最长 30 秒。建议使用人物始终在画面内的连续单镜头视频。
- `mode`：生成视频的模式，主要有标准模式 `std` 和极速模式 `pro` 俩种。
- `keep_original_sound`：可选择是否保留视频原声，枚举值：yes，no。
- `character_orientation`：生成视频中人物的朝向，可选择与图片一致或与视频一致，枚举值：image，video。
- `prompt`：提示词。
- `callback_url`：需要回调结果的URL。
- `async`：可选，设为 `true` 时接口立即返回 `task_id`，无需提供 `callback_url`，随后通过对应的任务查询接口轮询获取结果。

选择之后，可以发现右侧也生成了对应代码，如图所示：

<p><img src="https://cdn.acedata.cloud/buwczd.png" width="500" class="m-auto"></p>

点击「Try」按钮即可进行测试，如上图所示，这里我们就得到了如下结果：

```json
{
  "success": true,
  "video_id": "842578800134742051",
  "video_url": "https://cdn.acedata.cloud/assets/examples/gemini/04a043bd-6b23-4b4e-945c-ce48158c3eee-3a89912507c7.mp4",
  "duration": "5.066",
  "state": "succeed",
  "task_id": "363c7a84-e880-472e-a4d4-098e50cfc292"
}
```

返回结果一共有多个字段，介绍如下：

- `success`，此时视频生成任务的状态情况。
- `task_id`，此时视频生成任务ID。
- `video_id`，此时视频生成任务的视频ID。
- `video_url`，此时视频生成任务的视频链接。
- `duration`，此时视频生成任务的视频链时长。
- `state`，此时视频生成任务的状态。

可以看到我们得到了满意的视频信息，我们只需要根据结果中 `data` 的视频链接地址获取生成的Kling视频即可。

另外如果想生成对应的对接代码，可以直接复制生成，例如 CURL 的代码如下：

```shell
curl -X POST 'https://api.acedata.cloud/kling/motion' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "image_url": "https://cdn.acedata.cloud/e724d7f13d.png",
  "video_url": "https://cdn.acedata.cloud/odwfm5.mp4",
  "prompt": "让画面生动起来",
  "mode": "std",
  "character_orientation": "image"
}'
```

## 异步回调

由于 Kling Motion Generation API生成的时间相对较长，大约需要 1-2 分钟，如果 API 长时间无响应，HTTP 请求会一直保持连接，导致额外的系统资源消耗，所以本 API 也提供了异步回调的支持。

整体流程是：客户端发起请求的时候，额外指定一个 `callback_url` 字段，客户端发起 API 请求之后，API 会立马返回一个结果，包含一个 `task_id` 的字段信息，代表当前的任务 ID。当任务完成之后，生成视频的结果会通过 POST JSON 的形式发送到客户端指定的 `callback_url`，其中也包括了 `task_id` 字段，这样任务结果就可以通过 ID 关联起来了。

下面我们通过示例来了解下具体怎样操作。

首先，Webhook 回调是一个可以接收 HTTP 请求的服务，开发者应该替换为自己搭建的 HTTP 服务器的 URL。此处为了方便演示，使用一个公开的 Webhook 样例网站 https://webhook.site/，打开该网站即可得到一个 Webhook URL，如图所示：

![](https://cdn.acedata.cloud/tbcnai.png)

将此 URL 复制下来，就可以作为 Webhook 来使用，此处的样例为 `https://webhook.site/624b2c78-6dbd-4618-9d2b-b32eade6d8c3`。

接下来，我们可以设置字段 `callback_url` 为上述 Webhook URL，同时填入相应的参数，具体的内容如图所示：

<p><img src="https://cdn.acedata.cloud/vdx12s.png" width="500" class="m-auto"></p>

点击运行，可以发现会立即得到一个结果，如下：

```
{
  "task_id": "20068983-0cc9-4c6a-aeb6-9c6a3c668be0"
}
```

稍等片刻，我们可以在 `https://webhook.site/624b2c78-6dbd-4618-9d2b-b32eade6d8c3` 上观察到生成视频的结果，如图所示：

![](https://cdn.acedata.cloud/zv5u2q.png)

内容如下：

```json
{
    "success": true,
    "video_id": "030bb06d-98d4-4044-9042-0aa0822e8c8c",
    "video_url": "https://cdn.acedata.cloud/assets/examples/gemini/04a043bd-6b23-4b4e-945c-ce48158c3eee-3a89912507c7.mp4",
    "duration": "5.1",
    "state": "succeed",
    "task_id": "20068983-0cc9-4c6a-aeb6-9c6a3c668be0"
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

通过本文档，您已经了解了如何使用 Kling Motion Generation API 实现Kling官方的动作控制功能。希望本文档能帮助您更好地对接和使用该 API。如有任何问题，请随时联系我们的技术支持团队。
