# Fish TTS API 对接说明

本接口提供文本转语音、已保存声音调用和一次性即时声音克隆，地址为 `POST https://api.acedata.cloud/fish/tts`。

## 申请流程

要使用 Fish TTS API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Fish TTS API →](https://platform.acedata.cloud/services/fish)

## 请求头

| Header          | 必填 | 说明                                                            |
| --------------- | ---- | --------------------------------------------------------------- |
| `authorization` | 是   | `Bearer {token}`，`{token}` 是在本平台申请的密钥。              |
| `content-type`  | 是   | `application/json`。                                            |
| `accept`        | 否   | `application/json`。                                            |
| `model`         | 否   | TTS 模型，可选 `s1`、`s2-pro` 或 `s2.1-pro`，默认 `s2-pro`。`s2.1-pro` 为最新一代，`s2-pro` 表现力强；`s1` 更稳定，长文本不易跑偏。三者同价。 |

## 请求体字段

| 字段                 | 类型           | 必填 | 说明                                                                                                                                                                          |
| -------------------- | -------------- | ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `text`               | string         | 是   | 要合成的文本，非空字符串。                                                                                                                                                   |
| `format`             | string         | 否   | 输出音频格式，可选 `mp3`（默认）、`wav`、`pcm`。`wav` 与 `pcm` 返回的都是 WAV 容器。`opus` 不受支持，传入会直接返回 `400`。                              |
| `reference_id`       | string \| string[] | 否 | 已保存或公共声音的模型 ID，可由 [Fish Model API](https://platform.acedata.cloud/documents/fish-model) 创建，或在 [Fish Model Query](https://platform.acedata.cloud/documents/fish-model-query) 中检索。不能与 `references` 同时使用。 |
| `references`         | object[]       | 否   | 一次性即时声音克隆，仅支持一个 `{audio, text}` 样本：`audio` 是公开 HTTPS MP3/WAV URL，`text` 是音频的准确逐字稿。不能与 `reference_id` 同时使用。                                                                                          |
| `sample_rate`        | integer        | 否   | 采样率，常用 `16000`、`22050`、`44100`。`format=mp3` 默认 44100。                                                                                                            |
| `mp3_bitrate`        | integer        | 否   | MP3 码率，可选 `64`、`128`、`192`。仅 `format=mp3` 生效。                                                                                                                    |
| `prosody`            | object         | 否   | 韵律覆盖，支持 `speed`（语速，1.0 为原速）和 `volume`（音量增益 dB）。例如 `{"speed":1.2,"volume":0}`。                                                                       |
| `chunk_length`       | integer        | 否   | 上游分片长度，默认上游决定。                                                                                                                                                 |
| `temperature`        | number         | 否   | 采样温度，范围约 0.0–1.0。                                                                                                                                                   |
| `top_p`              | number         | 否   | top-p 采样参数。                                                                                                                                                            |
| `latency`            | string         | 否   | `normal` 或 `balanced`，缺省由本接口自动补 `normal`（直接传空字符串上游会拒绝）。                                                                                            |
| `normalize`          | boolean        | 否   | 是否对文本做归一化。                                                                                                                                                         |
| `callback_url`       | string         | 否   | 异步回调地址，详见下文「异步回调」。**这是相对官方接口的扩展**。                                                                                                             |

> 一次性克隆只接受 HTTPS 音频 URL，不接受 MessagePack、Base64、data URI 或带凭据的 URL。参考音频建议 10–270 秒；Studio 使用更保守的 10–60 秒范围。

## 示例 1：最小请求（`text` + `format=mp3`）

```shell
curl -X POST 'https://api.acedata.cloud/fish/tts' \
  -H 'authorization: Bearer {token}' \
  -H 'content-type: application/json' \
  -d '{
    "text": "Hello world.",
    "format": "mp3"
  }'
```

返回（实测）：

```json
{
  "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/e2ffcc06-18da-4a8c-b9aa-9337d0f9ec1d-230825dfc559.mp3"
}
```

`audio_url` 指向本平台 CDN，可直接 GET 下载或在 `<audio>` 中播放。最终成功响应还会返回顶层 `cost`，其中 `amount` 是本次实际扣除的 Credits；如有账户折扣，`list_amount` 表示折扣前额度。链接长期可用，但仍建议在你自己的存储里留一份。

## 示例 2：使用克隆音色 `reference_id`

下面用 Fish 平台上一个公开的西班牙语音色（`_id` 可通过 [Fish Model Query](https://platform.acedata.cloud/documents/fish-model-query) 检索得到）：

```shell
curl -X POST 'https://api.acedata.cloud/fish/tts' \
  -H 'authorization: Bearer {token}' \
  -H 'content-type: application/json' \
  -d '{
    "text": "Hermanos míos, hoy es un buen día.",
    "reference_id": "8d2c17a9b26d4d83888ea67a1ee565b2",
    "format": "mp3"
  }'
```

返回（实测）：

```json
{
  "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/b6f161f2-a100-4818-add2-47694f234659-6532864739de.mp3"
}
```

## 示例 3：一次性即时声音克隆（`references`）

将参考音频放在公开 HTTPS 地址，并提供其中实际说出的准确原文。该声音只用于本次合成，不会创建长期模型：

```shell
curl -X POST 'https://api.acedata.cloud/fish/tts' \
  -H 'authorization: Bearer {token}' \
  -H 'content-type: application/json' \
  -H 'model: s2-pro' \
  -d '{
    "text": "新的旅程从这一刻开始，让我们一起向前。",
    "format": "mp3",
    "references": [{
      "audio": "https://cdn.acedata.cloud/assets/examples/fish/6220d605-39d0-4d43-9e58-0f12949dc9b9-570cfdf96ad9.mp3",
      "text": "春天的清晨，阳光穿过树叶，落在安静的小路上。"
    }]
  }'
```

实测成功响应：

```json
{
  "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/995dfe37-b187-474d-8323-b08d6678ed8f-6359be9f8873.mp3",
  "cost": {"amount": 0.007609319999999999, "currency": "credit"}
}
```

| 方式 | 生命周期 | 适用场景 |
| --- | --- | --- |
| `references` | 仅本次 TTS 请求 | 临时使用或每次声音不同 |
| `reference_id` | 可重复使用 | 公共声音或通过 `/fish/model` 创建的长期声音 |

## 示例 3：调节语速 / 音量（`prosody`）

```shell
curl -X POST 'https://api.acedata.cloud/fish/tts' \
  -H 'authorization: Bearer {token}' \
  -H 'content-type: application/json' \
  -d '{
    "text": "Faster speech with prosody overrides.",
    "prosody": { "speed": 1.2, "volume": 0 },
    "format": "mp3"
  }'
```

返回（实测）：

```json
{
  "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3"
}
```

`speed` 大于 1 加快，小于 1 减慢；`volume` 单位 dB，0 表示不变，正数增益，负数衰减。

## 示例 5：切换模型 + 控制码率

通过 HTTP 头 `model: s1` 切换到稳定型模型，请求体中加 `mp3_bitrate: 128` 控制 MP3 码率：

```shell
curl -X POST 'https://api.acedata.cloud/fish/tts' \
  -H 'authorization: Bearer {token}' \
  -H 'content-type: application/json' \
  -H 'model: s1' \
  -d '{
    "text": "high bitrate mp3",
    "format": "mp3",
    "mp3_bitrate": 128
  }'
```

返回（实测）：

```json
{
  "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/7e7abf3d-3d72-4c9f-8eb6-8af932d7c96e-6f11bf2f30e9.mp3"
}
```

## 示例 6：PCM 原始波形

需要在浏览器里做实时拼接、或在客户端做后续处理（混音、变速）的场景，推荐使用 `pcm`：

```shell
curl -X POST 'https://api.acedata.cloud/fish/tts' \
  -H 'authorization: Bearer {token}' \
  -H 'content-type: application/json' \
  -d '{
    "text": "hi",
    "format": "pcm",
    "sample_rate": 16000
  }'
```

返回（实测）：

```json
{
  "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/64adc04b-c196-4a0f-9070-222ba101ce6c-fc50de38c165.wav"
}
```

> 链接的扩展名跟随请求里的 `format`：`mp3` 得到 `.mp3`，`wav` 与 `pcm` 得到 `.wav`（WAV 容器，16 bit PCM）。

## 异步回调（`callback_url`）

长文本一次合成可能需要十几秒到几十秒，连接如果中断需要重试。请求体中传 `callback_url` 后，接口会立即返回 `{task_id, started_at}`，上游真正完成时把完整结果以 POST JSON 形式回调到该 URL，请求体中带同一个 `task_id` 和本次最终计费的顶层 `cost`。初始任务确认尚未完成合成，因此不包含 `cost`。

```shell
curl -X POST 'https://api.acedata.cloud/fish/tts' \
  -H 'authorization: Bearer {token}' \
  -H 'content-type: application/json' \
  -d '{
    "text": "今天天气真好，我们一起出去散散步吧。",
    "format": "mp3",
    "callback_url": "https://webhook.site/4815f79f-a40f-4078-ac85-1cc126b6bb34"
  }'
```

立即返回（实测）：

```json
{
  "task_id": "79d82713-2897-4eeb-9934-e7544d471aa7",
  "started_at": 1778462584.742
}
```

稍后 `callback_url` 会收到形如：

```json
{
  "task_id": "79d82713-2897-4eeb-9934-e7544d471aa7",
  "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/bd66b8c5-7543-4557-b684-baa72407e336-52f2e79732f2.mp3"
}
```

也可以用 [Fish Tasks API](https://platform.acedata.cloud/documents/fish-tasks) 主动按 `task_id` 拉取结果；终态记录的 `response.cost` 与回调中的 `cost` 一致，详见该文档。

## 错误处理

- `400 token_mismatched`：请求参数缺失或不合法（最常见是 `text` 为空，或 `format` 传了 `mp3`/`wav`/`pcm` 之外的值）。
- `401 invalid_token`：鉴权 token 不存在或无效。
- `429 too_many_requests`：触发账号速率限制。
- `500 api_error`：服务器内部错误。

错误响应示例：

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

参数校验错误会在 `message` 字段说明不合法的字段，例如：

```json
{
  "status": 400,
  "message": "[{\"type\":\"literal_error\",\"loc\":[\"format\"],\"msg\":\"Input should be 'pcm' or 'mp3'\",\"input\":\"wav\"}]"
}
```

## 结论

接入 Fish TTS 的最小代价是：在已有 TTS 调用中使用 `https://api.acedata.cloud/fish/tts` 和本平台 token，并在请求体里**显式带上** `format: "mp3"`。长文本场景建议使用 `callback_url` 异步回调；对克隆音色 `reference_id` 的发现，请配合 [Fish Model Query](https://platform.acedata.cloud/documents/fish-model-query) 与 [Fish Model Get](https://platform.acedata.cloud/documents/fish-model-get)。
