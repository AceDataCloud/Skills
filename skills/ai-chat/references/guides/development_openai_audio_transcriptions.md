# OpenAI 语音识别 API（/v1/audio/transcriptions）

将音频转写为文字，**完全兼容 OpenAI 的 `/v1/audio/transcriptions`**。任何 OpenAI SDK 只需把 `base_url` 指向 `https://api.acedata.cloud`、把密钥换成你的 AceData Token 即可直接使用。支持普通完整响应，也支持 `gpt-transcribe` 的 SSE 增量转写。

- **请求地址**：`POST https://api.acedata.cloud/v1/audio/transcriptions`（别名 `POST /openai/audio/transcriptions`）
- **鉴权**：请求头 `Authorization: Bearer {token}`
- **请求格式**：`multipart/form-data`
- **计费**：按音频时长计费（见下表），不足 1 秒按 1 秒计。

## 请求参数

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `file` | file | 是 | 待转写的音频文件，最大 25 MB。支持 `flac`、`mp3`、`mp4`、`mpeg`、`mpga`、`m4a`、`ogg`、`wav`、`webm`。 |
| `model` | string | 否 | `whisper-1`（默认）或 `gpt-transcribe`，能力差异见下表。 |
| `language` | string | 否 | 音频语种，ISO-639-1 代码（如 `zh`、`en`）。填写可提升准确率与速度；留空则自动识别。 |
| `prompt` | string | 否 | 提示词，用于引导书写风格，或提供专有名词、术语以提升识别准确率。 |
| `response_format` | string | 否 | `whisper-1`：`json`（默认）、`text`、`srt`、`verbose_json`、`vtt`；`gpt-transcribe`：仅 `json`、`text`。 |
| `temperature` | number | 否 | 采样温度 0–1，默认 0。 |
| `timestamp_granularities[]` | array | 否 | 时间戳粒度，`word` 或 `segment`，需配合 `response_format=verbose_json` 使用。 |
| `languages[]` | array | 否 | 候选语种（ISO-639-1），**仅 `gpt-transcribe`**。与 `language` 互斥，不要同时传。 |
| `keywords[]` | array | 否 | 专有名词/术语提示，**仅 `gpt-transcribe`**，可显著提升品牌名、人名的识别准确率。 |
| `stream` | boolean | 否 | `gpt-transcribe` 设为 `true` 时返回 SSE 增量事件；`whisper-1` 会忽略该参数并返回完整结果（与 OpenAI 官方行为一致）。 |

## 选哪个模型

| | `whisper-1` | `gpt-transcribe` |
| --- | --- | --- |
| 价格 | $0.0078 / 分钟 | **$0.0059 / 分钟**（更便宜） |
| 识别准确率 | 良好 | **更好**，尤其是品牌名、专有名词 |
| 字幕输出（`srt`/`vtt`） | ✅ | ❌ |
| 词级时间戳 | ✅ | ❌ |
| `languages[]` / `keywords[]` | ❌ | ✅ |
| 返回检测到的语种 | 需 `verbose_json` | 默认返回 |
| SSE 增量返回 | ❌（`stream` 被忽略） | ✅ |

**需要字幕或词级时间戳 → `whisper-1`；其余场景推荐 `gpt-transcribe`**（更准且更便宜）。

## 示例

```shell
curl -X POST 'https://api.acedata.cloud/v1/audio/transcriptions' \
  -H 'authorization: Bearer {token}' \
  -F file=@audio.mp3 \
  -F model=whisper-1
```

返回：

```json
{
  "text": "Ace Data Cloud Platform is testing the speech recognition endpoint. The quick brown fox jumps over the lazy dog."
}
```

中文音频同样支持，无需指定语种：

```json
{
  "text": "欢迎使用 AceData Cloud 平台,我们正在测试语音识别接口,今天是 7 月 31 号。"
}
```

### 生成字幕

把 `response_format` 设为 `srt` 或 `vtt`，直接得到可用的字幕文件：

```shell
curl -X POST 'https://api.acedata.cloud/v1/audio/transcriptions' \
  -H 'authorization: Bearer {token}' \
  -F file=@audio.mp3 \
  -F model=whisper-1 \
  -F response_format=srt \
  -o subtitle.srt
```

返回内容（`Content-Type: text/plain`）：

```
1
00:00:00,000 --> 00:00:03,800
Ace Data Cloud Platform is testing the speech recognition endpoint.

2
00:00:03,800 --> 00:00:06,280
The quick brown fox jumps over the lazy dog.
```

### 词级时间戳

需要每个词的起止时间时，用 `verbose_json` 搭配 `timestamp_granularities[]=word`：

```shell
curl -X POST 'https://api.acedata.cloud/v1/audio/transcriptions' \
  -H 'authorization: Bearer {token}' \
  -F file=@audio.mp3 \
  -F model=whisper-1 \
  -F response_format=verbose_json \
  -F 'timestamp_granularities[]=word'
```

返回：

```json
{
  "task": "transcribe",
  "language": "english",
  "duration": 6.29,
  "text": "Ace Data Cloud Platform is testing the speech recognition endpoint. The quick brown fox jumps over the lazy dog.",
  "words": [
    { "word": "Ace", "start": 0.0, "end": 0.32 },
    { "word": "Data", "start": 0.32, "end": 0.54 },
    { "word": "Cloud", "start": 0.54, "end": 0.86 }
  ]
}
```

### 流式转写

`gpt-transcribe` 可通过 `stream=true` 返回 `Content-Type: text/event-stream`。服务会原样发送 OpenAI 兼容事件：
`transcript.text.delta` 携带增量文字，`transcript.text.done` 携带完整文字和 `usage` 并表示正常完成。

```shell
curl -N -X POST 'https://api.acedata.cloud/v1/audio/transcriptions' \
  -H 'authorization: Bearer {token}' \
  -F file=@audio.mp3 \
  -F model=gpt-transcribe \
  -F stream=true
```

事件流示例：

```text
data: {"type":"transcript.text.delta","delta":"Hello"}

data: {"type":"transcript.text.done","text":"Hello world","usage":{"type":"tokens","input_tokens":14,"output_tokens":3,"total_tokens":17}}
```

收到 `transcript.text.done` 才表示正常完成。若流建立后处理失败，连接会在 `event: error` 事件后结束；客户端主动断开会取消本次处理，不会继续在后台生成。`whisper-1` 即使传入 `stream=true` 也仍按普通非流式响应返回。

### 使用官方 SDK

```python
from openai import OpenAI

client = OpenAI(base_url="https://api.acedata.cloud/v1", api_key="{token}")
with open("audio.mp3", "rb") as f:
    result = client.audio.transcriptions.create(model="whisper-1", file=f)
print(result.text)
```

## 价格

| 模型 | 本平台价 |
| --- | --- |
| `whisper-1` | $0.0078 / 分钟 |
| `gpt-transcribe` | $0.0059 / 分钟 |

> 按音频实际时长计费，不足 1 秒按 1 秒计，单次最长按 1 小时封顶。

## 注意事项

- 单个文件最大 **25 MB**。超过请先分段或压缩（降低码率通常即可，语音识别对音质要求不高）。
- `gpt-transcribe` 支持 `stream=true` SSE；`whisper-1` 会忽略 `stream` 并返回完整结果。
- 参数与 OpenAI 官方 `/v1/audio/transcriptions` 保持一致，官方 SDK 只需改 `base_url` 即可使用。
- `include[]`、`chunking_strategy`、`known_speaker_names[]`、`known_speaker_references[]` 属于我们未上架的
  转写模型，传入会返回 400 而不是静默忽略。模型专属参数（`timestamp_granularities[]` 之于 `whisper-1`、
  `languages[]`/`keywords[]` 之于 `gpt-transcribe`）传给不支持的模型时同样返回 400。
- 请求较为耗时，建议客户端超时设置不低于 300 秒。

## 错误码

| 状态码 | code | 说明 |
| --- | --- | --- |
| 400 | `bad_request` | 未提供 `file`、文件无法解析，或参数非法（`model`/`response_format` 取值不支持、`temperature` 超出 0–1、`timestamp_granularities[]` 未配合 `verbose_json`、传入了 `whisper-1` 不支持的参数）。 |
| 401 | `authentication_failed` | token 无效。 |
| 403 | `used_up` | 余额不足。 |
| 413 | `request_too_large` | 音频文件超过 25 MB 上限。 |
| 429 | `too_many_requests` | 请求过于频繁，请稍后重试。 |
| 500 | `api_error` | 服务内部错误，请稍后重试。 |
