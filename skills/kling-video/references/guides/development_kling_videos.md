# Kling Videos Generation API 对接说明

本文将介绍一种 Kling Videos Generation API 对接说明，它是可以通过输入自定义参数来生成Kling官方的视频。

## 申请流程

要使用 Kling Videos Generation API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Kling Videos Generation API →](https://platform.acedata.cloud/documents/kling-videos)

## 基本使用

首先先了解下基本的使用方式，就是输入提示词 `prompt`、 生成行为 `action`、首帧参考图片 `start_image_url` 以及模型 `model`，便可获得处理后的结果，首先需要简单地传递一个 `action` 字段，它的值为 `text2video`，它主要包含三种行为：文生视频（`text2video`）、图生视频（`image2video`）、扩展视频（`extend`），然后我们还需要输入模型 `model`，目前主要有 `kling-v1`, `kling-v1-6`, `kling-v2-master`, `kling-v2-1-master`, `kling-v2-5-turbo`, `kling-v2-6`, `kling-v3`, `kling-v3-omni`, `kling-o1` 模型，具体的内容如下：

<p><img src="https://cdn.acedata.cloud/ke1bok.png" width="500" class="m-auto"></p>

可以看到这里我们设置了 Request Headers，包括：

- `accept`：想要接收怎样格式的响应结果，这里填写为 `application/json`，即 JSON 格式。
- `authorization`：调用 API 的密钥，申请之后可以直接下拉选择。

另外设置了 Request Body，包括：

- `model`：生成视频的模型，主要有 `kling-v1`, `kling-v1-6`, `kling-v2-master`, `kling-v2-1-master`, `kling-v2-5-turbo`, `kling-v2-6`, `kling-v3`, `kling-v3-omni`, `kling-o1` 模型。
- `mode`：生成视频的模式，可选值为标准模式 `std`、极速模式 `pro` 和原生 4K 模式 `4k`。其中 `4k` 仅支持 `kling-v3` 和 `kling-v3-omni`，且与 `camera_control`（运镜控制）不兼容。
- `action`：此次视频生成任务的行为，主要包含三种行为，分别为：文生视频（`text2video`）、图生视频（`image2video`）、扩展视频（`extend`）。
- `start_image_url`：当选择图生视频行为 `image2video` 就必须需要上传的首帧参考图片链接。
- `end_image_url`：图生视频时可选，指定尾帧。
- `duration`：视频时长，单位秒。`kling-v3` 和 `kling-v3-omni` 支持 3-15 秒整数时长；`kling-o1` 仅支持 5 秒；其他模型支持 5 或 10 秒。
- `generate_audio`：是否同步生成音频，可选，布尔值。支持 `kling-v3`、`kling-v3-omni` 以及 `kling-v2-6`（仅 pro 模式）。默认为 `false`。
- `aspect_ratio`：视频宽高比，可选，支持 `16:9`、`9:16`、`1:1`，默认 `16:9`。
- `cfg_scale`：相关性强度，范围 [0,1]，越大越贴合提示词。
- `camera_control`：可选，控制相机运动的对象参数，支持 type/simple 预设以及 horizontal、vertical、pan、tilt、roll、zoom 等配置。
- `negative_prompt`：可选，不希望出现的反向提示词，最多 200 字符。
- `image_list`：Omni 参考图片列表，适用模型 `kling-o1` 和 `kling-v3-omni`，用法见下文「Omni 全能参考」。
- `video_list`：Omni 参考视频列表（支持视频编辑），适用模型 `kling-o1` 和 `kling-v3-omni`，用法见下文「Omni 全能参考」。
- `prompt`：提示词。
- `callback_url`：需要回调结果的URL。
- `async`：可选，设为 `true` 时接口立即返回 `task_id`，无需提供 `callback_url`，随后通过对应的任务查询接口轮询获取结果。

选择之后，可以发现右侧也生成了对应代码，如图所示：

<p><img src="https://cdn.acedata.cloud/3yjql0.png" width="500" class="m-auto"></p>

点击「Try」按钮即可进行测试，如上图所示，这里我们就得到了如下结果：

```json
{
  "success": true,
  "video_id": "900798310464749610",
  "video_url": "https://cdn.acedata.cloud/assets/examples/kling/6c68c267-065b-4423-b66b-a0e4c59ee0d5-6a664a591a53.mp4",
  "duration": "5.041",
  "state": "succeed",
  "task_id": "6c68c267-065b-4423-b66b-a0e4c59ee0d5"
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
curl -X POST 'https://api.acedata.cloud/kling/videos' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "action": "text2video",
  "model": "kling-v3",
  "prompt": "White ceramic coffee mug on glossy marble countertop with morning window light. Camera slowly rotates 360 degrees around the mug, pausing briefly at the handle."
}'
```

## 模型能力矩阵

不同模型对参数的支持情况差异较大。以下矩阵整理自 [Kling 官方 video models 文档](https://app.klingai.com/global/dev/document-api/apiReference/model/videoModels)，调用前请先核对当前 `model` / `mode` / `duration` 组合是否支持你所需的功能，否则会返回 `model/mode/duration(...) is not supported with image_tail` 等错误。

| 模型 | 模式 | `end_image_url`（首尾帧） | `generate_audio`（伴音） | `camera_control`（运镜） | 备注 |
|---|---|---|---|---|---|
| `kling-v1` | std / pro | ✅ 仅 `duration=5` | ❌ | ✅ 仅 `duration=5` | `extend` 不支持 `negative_prompt` 与 `cfg_scale` |
| `kling-v1-6` | std | ❌ | ❌ | ❌ | 多图生视频、`extend` 全模式可用 |
| `kling-v1-6` | pro | ✅ | ❌ | ❌ | |
| `kling-v2-master` | — | ❌ | ❌ | ❌ | 单一模式，仅 `duration=5/10` |
| `kling-v2-1-master` | — | ❌ | ❌ | ❌ | 单一模式，仅 `duration=5/10` |
| `kling-v2-5-turbo` | std | ❌ | ❌ | ❌ | |
| `kling-v2-5-turbo` | pro | ✅ | ❌ | ❌ | |
| `kling-v2-6` | std | ❌ | ❌ | ❌ | |
| `kling-v2-6` | pro | ✅ | ✅ | ❌ | 唯一同时支持伴音的非 v3 模型 |
| `kling-v3` | std / pro | ✅ | ✅ | ✅ | `duration` 范围 3–15 秒 |
| `kling-v3` | 4k | ✅ | ✅ | ❌ | 4K 模式与运镜不兼容 |
| `kling-v3-omni` | std / pro / 4k | ✅ | ✅ | ❌ | |
| `kling-o1` | std / pro | ✅ | ❌ | ❌ | 仅支持 `duration=5` |

注意事项：

- `mode=4k` 仅 `kling-v3` 与 `kling-v3-omni` 支持；并且与 `camera_control`（运镜）互斥。
- `end_image_url` 只能在 `action=image2video` 时配合 `start_image_url` 使用。仅传 `end_image_url`（无 `start_image_url`）会被拒绝。
- `kling-v3` / `kling-v3-omni` 接受任意 3–15 秒的整数 `duration`；`kling-o1` 仅接受 5；其余模型只接受 5 或 10。
- `generate_audio` 默认 `false`。仅 `kling-v3`、`kling-v3-omni` 和 `kling-v2-6`（pro 模式）支持。

## 扩展视频功能

如果想对已经生成的Kling视频进行继续生成的话，可以将参数 `action` 设置为 `extend` ，并且输入需要继续生成视频的 ID，视频 ID 的获取是根据基本使用来获取，如下图所示：

<p><img src="https://cdn.acedata.cloud/om6p6g.png" width="500" class="m-auto"></p>

这时候可以看到视频的 ID 为：

```
"video_id": "030bb06d-98d4-4044-9042-0aa0822e8c8c"
```

> 注意，这里的视频中 `video_id` 是生成后视频的 ID，如果你不知道如何生成视频，可以参考上文的基本使用来生成视频。

接下来我们要必须填下一步需要扩展的提示词来自定义生成视频，就可以指定如下内容：

- `model`：生成视频的模型，主要有 `kling-v1` 、`kling-v1-5` 和 `kling-v1-6` 模型。
- `mode`：生成视频的模式，可选值为标准模式 `std`、极速模式 `pro` 和原生 4K 模式 `4k`（仅 `kling-v3` 和 `kling-v3-omni` 支持，与运镜控制不兼容）。
- `duration`：此次视频生成任务的视频时长，主要包含5s和10s。
- `start_image_url`：当选择图生视频行为 `image2video` 就必须需要上传的首帧参考图片链接。
- `prompt`：提示词。

填写样例如下：

<p><img src="https://cdn.acedata.cloud/ejimqy.png" width="500" class="m-auto"></p>

填写完毕之后自动生成了代码如下：

<p><img src="https://cdn.acedata.cloud/52x4u5.png" width="500" class="m-auto"></p>

对应的 Python 代码：

```python
import requests

url = "https://api.acedata.cloud/kling/videos"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "action": "extend",
    "model": "kling-v1",
    "video_id": "030bb06d-98d4-4044-9042-0aa0822e8c8c",
    "prompt": "White ceramic coffee mug on glossy marble countertop with morning window light. Camera slowly rotates 360 degrees around the mug, pausing briefly at the handle.",
    "duration": 10
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

点击运行，可以发现会得到一个结果，如下：

```json
{
  "success": true,
  "video_id": "bbc3b105-ac72-4de2-8390-0cb37dc7d41e",
  "video_url": "https://cdn.acedata.cloud/assets/examples/gemini/04a043bd-6b23-4b4e-945c-ce48158c3eee-3a89912507c7.mp4",
  "duration": "9.6",
  "state": "succeed",
  "task_id": "3ece87e6-3ee3-4f5e-bd70-5ae5eca89a23"
}
```

可以看出，结果内容与上文的是一致的，这也就实现视频的扩展视频功能。

## Omni 全能参考（视频编辑 / 参考视频 / 多图参考）

`kling-o1` 与 `kling-v3-omni` 是两个独立模型，二者都支持「全能参考」能力。在文生视频（`action=text2video`）基础上，可额外传入参考图片或参考视频，实现**多图参考、参考视频以及直接编辑已有视频**。

**核心约定**：参考素材必须在 `prompt` 中以 `<<<image_1>>>`、`<<<video_1>>>` 的形式（序号从 1 开始）引用 `image_list` / `video_list` 中对应位置的素材，模型才会应用这些参考。若只传素材而不在提示词中引用，素材会被忽略。

> 安全说明：当前 API 不开放 `element_list`。Kling Element Library 的 ID 不是租户隔离的，在提供租户隔离的 Element Management API 之前，请使用 `image_list` 传入主体参考图。

Omni 请求不支持 `negative_prompt`、`cfg_scale` 或 `camera_control`，也不能使用 `mode=4k`。包含参考视频时，`generate_audio` 必须为 `false`。

### 参考视频与视频编辑（`video_list`）

`video_list` 用于传入参考视频，是本能力最常用的场景，数组元素字段如下：

- `video_url`：参考视频链接，不可为空。最多 1 个 MP4/MOV 视频，文件大小 ≤200MB，帧率 24–60fps。`kling-o1` 要求时长 3–10 秒、宽和高各 700–2160px；`kling-v3-omni` 要求时长 3–15.5 秒、宽和高各 700–4553px、总像素 ≤8,294,400、宽高比 0.4–2。
- `refer_type`：参考类型，可选 `base`（默认，**待编辑的基础视频**，即"直接对视频进行编辑"，可增删/修改元素、改构图、换风格、换颜色、换天气等）或 `feature`（**特征参考**，参考其风格 / 运镜 / 续拍下一镜头）。
- `keep_original_sound`：是否保留原视频音频，可选 `yes`（保留）或 `no`（移除）。

> 注意：存在参考视频时，`generate_audio` 需为 `false`。`refer_type=base` 的视频不可再指定首帧 / 尾帧。

对已有视频进行编辑（把视频改成动漫风格）的 CURL 示例如下：

```shell
curl -X POST 'https://api.acedata.cloud/kling/videos' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "action": "text2video",
  "model": "kling-o1",
  "mode": "std",
  "duration": 5,
  "prompt": "把 <<<video_1>>> 改成电影级动漫风格，保留原有的运动和构图",
  "video_list": [
    {
      "video_url": "https://cdn.acedata.cloud/your-reference-video.mp4",
      "refer_type": "base",
      "keep_original_sound": "no"
    }
  ]
}'
```

### 多图参考（`image_list`）

`image_list` 用于传入参考图片（元素 / 场景 / 风格等），数组元素字段如下：

- `image_url`：参考图片链接，不可为空。要求：格式 .jpg/.jpeg/.png；文件大小 ≤10MB；最短边 ≥300px；宽高比 1:2.5 ~ 2.5:1。
- `type`：可选。不传时作为纯参考图；传 `first_frame` / `end_frame` 时分别作为首帧 / 尾帧（等价于 `start_image_url` / `end_image_url`）。

使用时需在 `prompt` 中以 `<<<image_1>>>`、`<<<image_2>>>` 引用。数量限制：不存在参考视频时参考图片 ≤ 7；存在参考视频时参考图片 ≤ 4。仅传首 / 尾帧时也可直接用 `start_image_url` / `end_image_url`，但尾帧必须与首帧一起使用。

> 注意：若同时传入 `start_image_url` / `end_image_url` 与 `image_list`，首 / 尾帧会排在 `image_list` 之前，可能影响 `<<<image_N>>>` 的序号对应关系。建议二选一：需要首 / 尾帧时直接在 `image_list` 中用 `type` 指定，不要与 `start_image_url` / `end_image_url` 混用。

多图参考生成视频的 CURL 示例：

```shell
curl -X POST 'https://api.acedata.cloud/kling/videos' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "action": "text2video",
  "model": "kling-o1",
  "mode": "std",
  "duration": 5,
  "prompt": "让 <<<image_1>>> 里的人物站在 <<<image_2>>> 的场景中，电影感光线",
  "image_list": [
    { "image_url": "https://cdn.acedata.cloud/subject.png" },
    { "image_url": "https://cdn.acedata.cloud/scene.png" }
  ]
}'
```

## 异步回调

由于 Kling Videos Generation API生成的时间相对较长，大约需要 1-2 分钟，如果 API 长时间无响应，HTTP 请求会一直保持连接，导致额外的系统资源消耗，所以本 API 也提供了异步回调的支持。

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

通过本文档，您已经了解了如何使用 Kling Videos Generation API 可通过输入提示词以及首帧参考图片来生成视频。希望本文档能帮助您更好地对接和使用该 API。如有任何问题，请随时联系我们的技术支持团队。

### Kling 3.0 Turbo

`model="kling-v3-turbo"` 支持文生视频和首帧图生视频，时长为 3–15 秒的整数。`mode="std"` 输出 720p，`mode="pro"` 输出 1080p。该模型自带原生音频，不提供关闭开关；省略 `generate_audio` 或设置为 `true`。该模型不支持尾帧、运镜对象、独立负向提示词或 `cfg_scale`。请在 `prompt` 中直接描述需要或避免出现的内容。

### 多镜头视频

`kling-v3` 和 `kling-v3-omni` 支持 `multi_shot=true`。`shot_type="intelligence"` 根据 `prompt` 自动分镜；`shot_type="customize"` 通过 `multi_prompt` 提供 1–6 个分镜，每项包含从 1 连续递增的 `index`、最多 512 字的 `prompt` 和至少 1 秒的整数 `duration`。所有分镜时长之和必须等于总 `duration`。定制分镜不使用全局 `prompt`。多镜头按所选模型、画质、音频配置和总时长计费。
