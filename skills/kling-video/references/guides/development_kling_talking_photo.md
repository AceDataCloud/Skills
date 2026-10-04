# 可灵会说话的照片 API（Kling Talking Photo）

一键把**一张照片 + 一段音频**变成一段「会说话的视频」。服务内部自动完成两步:先用 image2video 让照片动起来,再用 lip-sync 按音频对口型。你只需调用**一次**。

- **接口地址**：`POST https://api.acedata.cloud/kling/talking-photo`
- **计费**：按时长,5 秒 **16.45 Credits**、10 秒 **30.45 Credits**(= image2video + lip-sync 合并价)

## 请求头

| 字段 | 值 |
| --- | --- |
| `authorization` | `Bearer ${API_KEY}` |
| `content-type` | `application/json` |

## 请求参数

| 参数 | 类型 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| `image_url` | string | 是 | — | 人物照片的公开 URL,建议清晰正脸 |
| `audio_url` | string | 是 | — | 驱动音频的公开 URL（.mp3/.wav/.m4a/.aac,≤5MB） |
| `prompt` | string | 否 | — | 照片动画化阶段的动作/表情提示词 |
| `model` | string | 否 | `kling-v2-1-master` | 照片动画化使用的 Kling 模型 |
| `duration` | integer | 否 | `5` | 视频时长（5 或 10 秒） |
| `mode` | string | 否 | `pro` | 动画化质量（std/pro） |
| `callback_url` | string | 否 | — | 传入或 `async=true` 则异步返回 task_id |
| `async` | boolean | 否 | `false` | 异步模式,配合 `/kling/tasks` 轮询或回调 |

## 请求示例

```bash
curl -X POST 'https://api.acedata.cloud/kling/talking-photo' \
  -H 'authorization: Bearer ${API_KEY}' \
  -H 'content-type: application/json' \
  -d '{
    "image_url": "https://cdn.acedata.cloud/4hfydw.jpg",
    "audio_url": "https://cdn.acedata.cloud/6f7d62b18b.wav",
    "duration": 5
  }'
```

## 响应示例

```json
{
  "success": true,
  "task_id": "0c0b4d3a-2f1e-4a6b-9c2d-2b3c4d5e6f70",
  "video_id": "895055968777281546",
  "video_url": "https://cdn.acedata.cloud/assets/examples/kling/6c68c267-065b-4423-b66b-a0e4c59ee0d5-6a664a591a53.mp4",
  "source_video_url": "https://cdn.acedata.cloud/assets/examples/gemini/04a043bd-6b23-4b4e-945c-ce48158c3eee-3a89912507c7.mp4",
  "duration": 5,
  "state": "succeed"
}
```

| 字段 | 说明 |
| --- | --- |
| `video_url` | 最终会说话的视频（已转存本平台 CDN） |
| `source_video_url` | 中间的照片动画视频（image2video 结果） |
| `video_id` | 可灵视频 ID |

## 注意事项

- 照片建议清晰正脸、单人。
- 音频时长建议不超过视频时长（5s/10s）。
- 计费在成功时发生;参数校验失败（4xx）不计费。
- 生成耗时约 4–6 分钟（两步),建议用 `async=true` + `/kling/tasks` 轮询。
