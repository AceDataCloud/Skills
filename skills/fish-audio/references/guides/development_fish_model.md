# Fish Model Create API 对接说明

本接口基于 [Fish Audio 官方 Model API](https://docs.fish.audio/resources/api-reference/model)，用于**基于一段音频样本创建一个可长期复用的克隆声音模型**。地址为 `POST https://api.acedata.cloud/fish/model`。

> 只需临时使用参考声音时，无需创建模型，可直接使用 [Fish TTS API](https://platform.acedata.cloud/documents/fish-tts) 的 `references` 一次性即时克隆。分页检索现有音色请参考 [Fish Model Query API](https://platform.acedata.cloud/documents/fish-model-query)；按 `_id` 查询单个音色详情请参考 [Fish Model Get API](https://platform.acedata.cloud/documents/fish-model-get)。

## 申请流程

要使用 Fish Model API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Fish Model API →](https://platform.acedata.cloud/services/fish)

## 请求体字段

| 字段                    | 类型       | 必填 | 说明                                                                                                                       |
| ----------------------- | ---------- | ---- | -------------------------------------------------------------------------------------------------------------------------- |
| `title`                 | string     | 是   | 音色名称，用于在控制台列表中识别。                                                                                          |
| `voices`                | string     | 是   | 音频样本的 HTTP(S) URL（**单个字符串**，不是数组）。本接口不支持 multipart/二进制上传，请先把音频放到任意可公开访问的对象存储。 |
| `description`           | string     | 否   | 音色描述。                                                                                                                |
| `cover_image`           | string     | 否   | 封面图 HTTP(S) URL。                                                                                                      |
| `tags`                  | string[]   | 否   | 公共库检索标签，例如 `["male","narration","zh"]`。                                                                         |
| `texts`                 | string[]   | 否   | 与样本对应的参考文本（用于纠正发音）。                                                                                     |
| `enhance_audio_quality` | boolean    | 否   | 训练前是否对样本做音质增强。                                                                                              |
| `generate_sample`       | boolean    | 否   | 训练完成后是否自动生成一段示例音频。                                                                                       |

> 字段与上游完全一致，请同时参考 [Fish 官方文档](https://docs.fish.audio/resources/api-reference/model)。

## 示例：创建一个私有克隆音色

```shell
curl -X POST 'https://api.acedata.cloud/fish/model' \
  -H 'authorization: Bearer {token}' \
  -H 'content-type: application/json' \
  -d '{
    "title": "我的克隆音色",
    "description": "用一段播客录音克隆的中文音色",
    "voices": "https://example.com/sample-voice.mp3",
    "cover_image": "https://cdn.acedata.cloud/e724d7f13d.png"
  }'
```

> 注意：`voices` 必须是**字符串**（单个音频 URL），不是数组。传成 `["..."]` 上游会拒绝。

成功响应直接返回 Fish 平台的 ModelEntity 对象（下例为我们实测过的最小可用音色，删去了部分长字段以便阅读）：

```json
{
  "_id": "e5c6db52c3ed417f9cb2e5a33fb04667",
  "type": "tts",
  "title": "copilot-smoke-test",
  "description": "smoke test from api.acedata.cloud",
  "cover_image": "coverimage/e5c6db52c3ed417f9cb2e5a33fb04667",
  "train_mode": "fast",
  "state": "trained",
  "tags": [],
  "samples": [
    {
      "title": "Default Sample",
      "text": "师父，[语气坚定]我真的受够了这山上的清冷日子！...",
      "task_id": "6a1bf398dfae49dca0e23159214342a0",
      "audio": "https://platform.r2.fish.audio/task/6a1bf398dfae49dca0e23159214342a0.mp3"
    }
  ],
  "created_at": "2026-05-10T03:52:55.601000Z",
  "updated_at": "2026-05-10T03:52:55.601000Z",
  "languages": ["zh"],
  "visibility": "public",
  "default_text": "师父，[语气坚定]我真的受够了这山上的清冷日子！...",
  "like_count": 0,
  "mark_count": 0,
  "shared_count": 0,
  "task_count": 0,
  "author": {
    "_id": "780f2b2f862d41a08c0507bbbda77eb6",
    "nickname": "Penny Conrad",
    "avatar": "avatars/780f2b2f862d41a08c0507bbbda77eb6.jpg"
  }
}
```

`_id` 即可作为后续 [Fish TTS API](https://platform.acedata.cloud/documents/fish-tts) 中 `reference_id` 字段的值，用于使用该克隆音色进行语音合成：

```shell
curl -X POST 'https://api.acedata.cloud/fish/tts' \
  -H 'authorization: Bearer {token}' \
  -H 'content-type: application/json' \
  -d '{
    "text": "你好，这是一段使用我刚创建的克隆音色合成的语音。",
    "reference_id": "e5c6db52c3ed417f9cb2e5a33fb04667",
    "format": "mp3"
  }'
```

## 样本要求

经验值（与上游一致，可参考 [Fish 官方文档](https://docs.fish.audio/resources/api-reference/model)）：

- 时长建议 30 秒以上，5 分钟以内效果最佳；超过 10 分钟边际收益不大。
- 采样率 16 kHz 及以上，单声道或立体声均可。
- 内容尽量干净：无背景音乐、回声、明显环境噪声；同一说话人。
- 格式建议 `mp3` / `wav`。

如果对样本质量没有把握，可以同时传 `enhance_audio_quality: true` 让上游先做音质增强。

## 计费说明

创建音色克隆模型（`POST /fish/model`）免费，不收取任何费用；音色的查询接口（[Fish Model Query](https://platform.acedata.cloud/documents/fish-model-query)、[Fish Model Get](https://platform.acedata.cloud/documents/fish-model-get)）同样不计费。费用仅在后续调用 [Fish TTS](https://platform.acedata.cloud/documents/fish-tts) 合成语音时按用量产生。

## 错误处理

- `400 token_mismatched`：请求参数缺失或不合法（最常见是 `voices` 不是 URL，或传成了数组）。
- `401 invalid_token`：鉴权 token 不存在或无效。
- `429 too_many_requests`：触发账号速率限制。
- `500 api_error`：服务器内部错误。

错误响应示例：

```json
{
  "success": false,
  "error": {
    "code": "api_error",
    "message": "voices is required and must be an HTTP(S) URL pointing to an audio file"
  },
  "trace_id": "2cf86e86-22a4-46e1-ac2f-032c0f2a4e89"
}
```

## 结论

调用本接口只需要准备一段可公开访问的样本音频 URL，把它放到 `voices` 字段即可拿到 `_id`，再喂给 `/fish/tts` 的 `reference_id` 就完成了端到端的「克隆 → 合成」。常见坑点是 `voices` 必须是字符串、不能是数组。
