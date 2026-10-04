# 可灵对口型 API（Kling Lip Sync）

让一段**已有的可灵视频**（5 秒或 10 秒）按音频或文本"开口说话"——即对口型（Lip Sync）。配合 `/kling/videos` 的 `image2video`（让照片动起来），即可串成完整的"**会说话的照片 / 数字人口播**"流程。

> 本接口是 AceDataCloud 提供的单步便捷封装，面向常见的音频/文本驱动场景；它不是 Kling 官方「人脸识别 → Advanced Lip Sync」多步接口的字段镜像。请以本页参数表为准。

- **接口地址**：`POST https://api.acedata.cloud/kling/lip-sync`
- **请求格式**：`application/json`
- **响应格式**：`application/json`
- **计费**：每次成功调用 **2.45 Credits**（固定）

## 请求头（Request Headers）

| 字段 | 值 | 说明 |
| --- | --- | --- |
| `authorization` | `Bearer ${API_KEY}` | 你的 API 密钥，[获取地址](https://platform.acedata.cloud) |
| `content-type` | `application/json` | 请求体格式 |
| `accept` | `application/json` | 响应格式 |

## 请求参数（Request Body）

| 参数 | 类型 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| `mode` | string | 是 | — | 生成模式。枚举：`audio2video`（音频驱动）、`text2video`（文本驱动） |
| `video_id` | string | 二选一 | — | 可灵生成视频的 ID（如 `/kling/videos` 的 image2video 返回的 `video_id`）。**仅支持 30 天内生成的 5s/10s 视频**。`video_id` 与 `video_url` 二选一，不可同时传 |
| `video_url` | string | 二选一 | — | 公网可访问的视频链接。约束：`.mp4`/`.mov`，≤100MB，时长 2–10s，仅 720p/1080p，边长 720–1920px。与 `video_id` 二选一 |
| `audio_url` | string | 条件 | — | 驱动音频的下载 URL，`audio2video` + `audio_type=url` 时必填。格式 `.mp3`/`.wav`/`.m4a`/`.aac`，≤5MB |
| `audio_type` | string | 否 | `url` | 音频传输方式。枚举：`url`、`file`（`audio2video` 时生效） |
| `audio_file` | string | 条件 | — | 音频文件的 Base64，`audio_type=file` 时必填。格式同上，≤5MB |
| `text` | string | 条件 | — | 要朗读的文本，`text2video` 时必填，**最多 120 字** |
| `voice_id` | string | 条件 | — | 音色 ID，`text2video` 时必填 |
| `voice_language` | string | 否 | `zh` | 音色语言。枚举：`zh`、`en`（`text2video` 时生效） |
| `voice_speed` | float | 否 | `1.0` | 语速，范围 `0.8`–`2.0`，精确到一位小数（`text2video` 时生效） |
| `callback_url` | string | 否 | — | 回调地址。传入此项或 `async=true` 则**异步模式**：立即返回 `task_id`，结果生成后回调 |
| `async` | boolean | 否 | `false` | 是否异步。`true` 时立即返回 `task_id`，配合 `/kling/tasks` 轮询或 `callback_url` 回调 |

## 请求示例

### 1）音频驱动（audio2video）

```bash
curl -X POST 'https://api.acedata.cloud/kling/lip-sync' \
  -H 'authorization: Bearer ${API_KEY}' \
  -H 'content-type: application/json' \
  -d '{
    "mode": "audio2video",
    "video_id": "895055164389466178",
    "audio_url": "https://cdn.acedata.cloud/6f7d62b18b.wav"
  }'
```

### 2）文本驱动（text2video）

```bash
curl -X POST 'https://api.acedata.cloud/kling/lip-sync' \
  -H 'authorization: Bearer ${API_KEY}' \
  -H 'content-type: application/json' \
  -d '{
    "mode": "text2video",
    "video_id": "895055164389466178",
    "text": "哥，好久不见，我一切都好，你要照顾好自己。",
    "voice_id": "genshin_vindi2",
    "voice_language": "zh",
    "voice_speed": 1.0
  }'
```

## 响应示例（同步成功）

```json
{
  "success": true,
  "task_id": "07a3ec65-9f7e-4a09-b7b7-282684082527",
  "video_id": "895055968777281546",
  "video_url": "https://cdn.acedata.cloud/assets/examples/kling/6c68c267-065b-4423-b66b-a0e4c59ee0d5-6a664a591a53.mp4",
  "duration": "4.966",
  "state": "succeed"
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `success` | boolean | 是否成功 |
| `task_id` | string | 本次任务 ID（可用于 `/kling/tasks` 查询） |
| `video_id` | string | 生成视频的可灵 ID（可作为下一次 `extend`/`lip-sync` 的输入） |
| `video_url` | string | 生成的说话视频 URL（已转存至本平台 CDN，长期有效） |
| `duration` | string | 视频时长（秒） |
| `state` | string | 任务状态：`succeed` / `failed` |

## 异步模式与查询

传入 `callback_url` 或 `async: true` 时，接口**立即返回** `task_id`；之后可：

- **轮询**：`POST /kling/tasks`，body `{ "action": "retrieve", "id": "<task_id>" }`（免费）
- **回调**：生成完成后，结果 POST 到你的 `callback_url`

## 完整流程：会说话的照片（image2video → lip-sync）

```bash
# 第 1 步：让照片动起来，拿到 video_id
curl -X POST 'https://api.acedata.cloud/kling/videos' \
  -H 'authorization: Bearer ${API_KEY}' -H 'content-type: application/json' \
  -d '{"model":"kling-v2-1-master","action":"image2video","start_image_url":"https://cdn.acedata.cloud/4hfydw.jpg","prompt":"look at camera, natural","duration":5,"mode":"pro"}'
# → { "video_id": "895055164389466178", ... }

# 第 2 步：用音频对口型
curl -X POST 'https://api.acedata.cloud/kling/lip-sync' \
  -H 'authorization: Bearer ${API_KEY}' -H 'content-type: application/json' \
  -d '{"mode":"audio2video","video_id":"895055164389466178","audio_url":"https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3"}'
# → { "video_url": "https://cdn.acedata.cloud/assets/examples/kling/6c68c267-065b-4423-b66b-a0e4c59ee0d5-6a664a591a53.mp4", ... }
```

## 错误响应

```json
{
  "success": false,
  "error": { "code": "bad_request", "message": "one of video_id or video_url is required" },
  "trace_id": "f07cab09-3c18-4d74-9030-64ee840d9f16",
  "task_id": "f490537f-2e5c-4739-8149-6252fba2091c"
}
```

| HTTP | code | 含义 |
| --- | --- | --- |
| 400 | `bad_request` | 参数缺失或非法（如未传 mode、video 与 audio 二选一冲突、text 超 120 字） |
| 401 | `authorization_missing` | 缺少或无效的 API 密钥 |
| 403 | `forbidden` | 内容被风控拦截 |
| 429 | `too_many_requests` | 上游并发限制，请稍后重试 |
| 500 | `api_error` | 上游或内部错误 |

## 注意事项

- `video_id` 必须是**30 天内**生成的可灵视频，且为 **5s 或 10s**；否则请用 `video_url` 传入符合约束的视频。
- 输入视频建议**清晰正脸、单人**，口型效果最佳。
- 音频/文本时长应与视频时长匹配（音频不超过视频长度）。
- 计费在**成功**时发生（2.45 Credits/次）；参数校验失败（4xx）不计费。
