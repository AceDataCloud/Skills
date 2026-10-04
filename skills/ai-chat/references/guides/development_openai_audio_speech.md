# OpenAI 语音合成 API（/v1/audio/speech）

将文本合成为自然语音，**完全兼容 OpenAI 的 `/v1/audio/speech`**。任何 OpenAI SDK 只需把 `base_url` 指向 `https://api.acedata.cloud`、把密钥换成你的 AceData Token 即可直接使用。接口同步返回音频字节流。

- **请求地址**：`POST https://api.acedata.cloud/v1/audio/speech`（别名 `POST /openai/audio/speech`）
- **鉴权**：请求头 `Authorization: Bearer {token}`
- **计费**：按请求文本字节数计费，约为 OpenAI 官方价的 85%（见下表）。

## 请求参数

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `input` | string | 是 | 要合成的文本。 |
| `model` | string | 否 | `tts-1`（更快）或 `tts-1-hd`（更高音质，默认）。 |
| `voice` | string | 否 | `alloy`、`echo`、`fable`、`onyx`、`nova`、`shimmer` 之一，默认 `alloy`。 |
| `response_format` | string | 否 | `mp3`(默认)、`opus`、`aac`、`flac`、`wav`、`pcm`。 |
| `speed` | number | 否 | 语速 0.25–4.0，默认 1.0。 |

## 示例

```shell
curl -X POST 'https://api.acedata.cloud/v1/audio/speech' \
  -H 'authorization: Bearer {token}' \
  -H 'content-type: application/json' \
  -o speech.mp3 \
  -d '{
    "model": "tts-1-hd",
    "input": "What if one API gave you every AI video model?",
    "voice": "nova",
    "response_format": "mp3"
  }'
```

返回的是音频文件本身（`Content-Type: audio/mpeg`），直接写入 `speech.mp3` 即可播放。

用官方 OpenAI Python SDK：

```python
from openai import OpenAI
client = OpenAI(base_url="https://api.acedata.cloud/v1", api_key="{token}")
client.audio.speech.create(model="tts-1-hd", voice="nova", input="Hello from AceData.").stream_to_file("speech.mp3")
```

## 价格

| 模型 | OpenAI 官方价 | 本平台价（约 85 折） |
| --- | --- | --- |
| `tts-1` | $15 / 100 万字符 | 约 $12.75 / 100 万字符 |
| `tts-1-hd` | $30 / 100 万字符 | 约 $25.5 / 100 万字符 |

> 按请求文本字节数计费;`official_price` 字段展示 OpenAI 官方价以便对比。

## 错误码

| 状态码 | code | 说明 |
| --- | --- | --- |
| 400 | `bad_request` | `input` 为空或参数非法。 |
| 401 | `authentication_failed` | token 无效。 |
| 403 | `used_up` | 余额不足。 |
| 429 | `too_many_requests` | 请求过于频繁。 |
| 500 | `api_error` | 上游/内部错误。 |
