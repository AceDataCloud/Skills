# Wan 视频生成 API

`POST https://api.acedata.cloud/wan/videos` 同时支持现有 Wan 2.6 模型和 `wan3.0-video`。Wan 3 根据 `media` 自动识别文本、首尾帧或参考素材模式。

## Wan 3 文生视频

```bash
curl -X POST 'https://api.acedata.cloud/wan/videos' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "wan3.0-video",
    "prompt": "A paper boat drifting through a neon city at night",
    "duration": 5,
    "resolution": "720P",
    "ratio": "16:9",
    "audio": true,
    "async": true
  }'
```

Wan 3 支持 2–30 秒整数或 `-1` 智能时长，分辨率为 `480P`、`720P`、`1080P`。

## 多媒体参考

```json
{
  "model": "wan3.0-video",
  "prompt": "Create a cinematic product reveal",
  "media": [
    {"type":"first_frame","url":"https://cdn.acedata.cloud/assets/examples/qwen-image/40d5c76b-2f84-4b04-9ea0-b706417ae622-bac6a9e9de22.png"},
    {"type":"last_frame","url":"https://cdn.acedata.cloud/assets/examples/qwen-image/7a5a490c-1d60-4498-a362-a9334148f460-a2a2c1afbf39.png"}
  ],
  "duration": 8,
  "resolution": "1080P",
  "ratio": "16:9",
  "async": true
}
```

`media.type` 支持：

- `first_frame` / `last_frame`
- `reference_image`
- `reference_video`
- `reference_audio`
- `file` / `link`

首尾帧模式和参考素材模式不能混用。参考视频最终按真实输入视频秒数加成功输出视频秒数结算；文本、图片和音频输入不增加视频秒数。

## 官方标准价

| 分辨率 | 价格 |
|---|---:|
| 480P | $0.05/秒 |
| 720P | $0.10/秒 |
| 1080P | $0.20/秒 |

## Wan 2.6 兼容

现有 `wan2.6-t2v`、`wan2.6-i2v`、`wan2.6-r2v` 与 flash 变体继续使用 `action`、`image_url`、`reference_video_urls` 等参数，调用路径不变。

## 异步与结果

设置 `async: true` 后立即获得 `task_id`，通过 `/wan/tasks` 获取终态。成功视频会转存至 AceDataCloud CDN，并在响应中返回真实 usage 与 cost。
