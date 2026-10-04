# Hailuo Videos Generation API 对接说明

本文将介绍一种 Hailuo Videos Generation API 对接说明，它是可以通过输入自定义参数来生成Hailuo官方的视频。

## 申请流程

要使用 Hailuo Videos Generation API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Hailuo Videos Generation API →](https://platform.acedata.cloud/documents/hailuo-videos-integration)

## 基本使用

首先先了解下基本的使用方式，就是输入提示词 `prompt`、 生成行为 `action`、首帧参考图片 `first_image_url` 以及模型 `model`，便可获得处理后的结果，首先需要简单地传递一个 `action` 字段，它的值为 `generate`，然后我们还需要输入模型，目前主要有图生视频模型 `minimax-i2v` 和文生视频模型 `minimax-t2v`，具体的内容如下：

<p><img src="https://cdn.acedata.cloud/7jyu0n.png" width="500" class="m-auto"></p>

可以看到这里我们设置了 Request Headers，包括：

- `accept`：想要接收怎样格式的响应结果，这里填写为 `application/json`，即 JSON 格式。
- `authorization`：调用 API 的密钥，申请之后可以直接下拉选择。

另外设置了 Request Body，包括：

- `model`：生成视频的模型，主要有图生视频模型 `minimax-i2v` 和文生视频模型 `minimax-t2v` 俩种。
- `action`：此次视频生成任务的行为。
- `first_image_url`：当选择图生视频模型 `minimax-i2v` 就必须需要上传的首帧参考图片链接，不支持Base64编码。
- `prompt`：提示词。
- `callback_url`：需要回调结果的URL。
- `async`：可选，设为 `true` 时接口立即返回 `task_id`，无需提供 `callback_url`，随后通过对应的任务查询接口轮询获取结果。

选择之后，可以发现右侧也生成了对应代码，如图所示：

<p><img src="https://cdn.acedata.cloud/8psuxw.png" width="500" class="m-auto"></p>

点击「Try」按钮即可进行测试，如上图所示，这里我们就得到了如下结果：

```json
{
  "success": true,
  "task_id": "baf1034c-684c-46be-ae6d-89ebb89b690d",
  "trace_id": "3221eb74-1a25-447a-ba69-7d9b310e306c",
  "data": [
    {
      "id": "0pv8yhe4fdrge0cmckpv23pd2g",
      "model": "minimax-t2v",
      "prompt": "Internal heat",
      "video_url": "https://platform.cdn.acedata.cloud/czjl/qoueLWBokF3ud6tdVD6VJTZuXTnK5HaMO2qAOS46Ef8VSBFUA/tmp9e3u11c1.output.mp4",
      "state": "succeeded"
    }
  ]
}
```

返回结果一共有多个字段，介绍如下：

- `success`，此时视频生成任务的状态情况。
- `task_id`，此时视频生成任务ID。
- `trace_id`，此时视频生成跟踪ID。
- `data`，此时视频生成任务的结果列表。
	- `id`，此时视频生成任务的视频ID。
	- `prompt`，此时视频生成任务的提示词。
	- `model`，此时视频生成任务的封面链接。
	- `video_url`，此时视频生成任务的视频链接。
	- `state`，此时视频生成任务的状态。

可以看到我们得到了满意的视频信息，我们只需要根据结果中 `data` 的视频链接地址获取生成的Hailuo视频即可。

另外如果想生成对应的对接代码，可以直接复制生成，例如 CURL 的代码如下：

```shell
curl -X POST 'https://api.acedata.cloud/hailuo/videos' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "action": "generate",
  "prompt": "Internal heat"
}'
```

## 异步回调

由于 Hailuo Videos Generation API生成的时间相对较长，大约需要 1-2 分钟，如果 API 长时间无响应，HTTP 请求会一直保持连接，导致额外的系统资源消耗，所以本 API 也提供了异步回调的支持。

整体流程是：客户端发起请求的时候，额外指定一个 `callback_url` 字段，客户端发起 API 请求之后，API 会立马返回一个结果，包含一个 `task_id` 的字段信息，代表当前的任务 ID。当任务完成之后，生成视频的结果会通过 POST JSON 的形式发送到客户端指定的 `callback_url`，其中也包括了 `task_id` 字段，这样任务结果就可以通过 ID 关联起来了。

下面我们通过示例来了解下具体怎样操作。

首先，Webhook 回调是一个可以接收 HTTP 请求的服务，开发者应该替换为自己搭建的 HTTP 服务器的 URL。此处为了方便演示，使用一个公开的 Webhook 样例网站 https://webhook.site/，打开该网站即可得到一个 Webhook URL，如图所示：

![](https://cdn.acedata.cloud/cjjfly.png)

将此 URL 复制下来，就可以作为 Webhook 来使用，此处的样例为 `https://webhook.site/580b81f5-596e-4321-b03f-606770b0bb83`。

接下来，我们可以设置字段 `callback_url` 为上述 Webhook URL，同时填入相应的参数，具体的内容如图所示：

<p><img src="https://cdn.acedata.cloud/odabh3.png" width="500" class="m-auto"></p>

点击运行，可以发现会立即得到一个结果，如下：

```
{
  "task_id": "05aff65c-5e84-442b-8e29-3a5d27130840"
}
```

稍等片刻，我们可以在 `https://webhook.site/580b81f5-596e-4321-b03f-606770b0bb83` 上观察到生成视频的结果，如图所示：

![](https://cdn.acedata.cloud/7jngb4.png)

内容如下：

```json
{
    "success": true,
    "task_id": "05aff65c-5e84-442b-8e29-3a5d27130840",
    "trace_id": "b9856b8a-725d-45c9-befe-e789d9fd9ffb",
    "data": [
        {
            "id": "t80jhsf96srg80cmcm6b0rk8gm",
            "model": "minimax-t2v",
            "prompt": "Internal heat",
            "video_url": "https://platform.cdn.acedata.cloud/czjl/YPaUz2DcwpJqItTXAG9XHAoEoj3dbF0XPU69LT5nefCMzBFUA/tmp8s_59jez.output.mp4",
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

通过本文档，您已经了解了如何使用 Hailuo Videos Generation API 可通过输入提示词以及首帧参考图片来生成视频。希望本文档能帮助您更好地对接和使用该 API。如有任何问题，请随时联系我们的技术支持团队。
