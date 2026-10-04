# Fish Model Get API 对接说明

本接口基于 [Fish Audio 官方 Model API](https://docs.fish.audio/resources/api-reference/model)，用于**按 `_id` 查询单个克隆音色的完整详情**。地址为 `GET https://api.acedata.cloud/fish/model/{id}`。

> 创建音色请参考 [Fish Model Create API](https://platform.acedata.cloud/documents/fish-model)；分页检索请参考 [Fish Model Query API](https://platform.acedata.cloud/documents/fish-model-query)。

## 申请流程

要使用 Fish Model API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Fish Model API →](https://platform.acedata.cloud/services/fish)

## 路径参数

| 参数 | 必填 | 说明                                                                                                                                                                  |
| ---- | ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id` | 是   | 音色的 `_id`（32 位十六进制字符串）。可通过 [Fish Model Create](https://platform.acedata.cloud/documents/fish-model) 创建时返回，或通过 [Fish Model Query](https://platform.acedata.cloud/documents/fish-model-query) 检索得到。 |

无请求体、无查询参数。

## 示例：拉取一个公开西班牙语音色的完整详情

```shell
curl 'https://api.acedata.cloud/fish/model/8d2c17a9b26d4d83888ea67a1ee565b2' \
  -H 'authorization: Bearer {token}'
```

返回（实测，删去了 `samples[].audio` 中的签名 query string 以便阅读）：

```json
{
  "_id": "8d2c17a9b26d4d83888ea67a1ee565b2",
  "type": "tts",
  "title": "Valentino Narración Biblica Fer",
  "description": "A mature and authoritative male voice with a calm, spiritual tone. It is well-suited for religious narration, educational content, and professional storytelling in Spanish.",
  "cover_image": "coverimage/8d2c17a9b26d4d83888ea67a1ee565b2",
  "train_mode": "fast",
  "state": "trained",
  "tags": [
    "male", "old", "narration", "calm", "serious",
    "authoritative", "professional", "clear", "Spanish"
  ],
  "samples": [
    {
      "title": "Default Sample",
      "text": "Hermanos míos, recordemos las palabras del Señor en estos tiempos difíciles. Como dice la Escritura, la fe mueve montañas, y el amor de Dios nos guía en cada paso del camino. Mantengamos firme nuestra confianza en Su divina providencia.",
      "task_id": "59ce7df6935c42249759327ddf70f37b",
      "audio": "https://c97f3361a1c971323738e24f451a0225.r2.cloudflarestorage.com/fish-platform-data/task/59ce7df6935c42249759327ddf70f37b.mp3?X-Amz-...signed..."
    }
  ],
  "created_at": "2025-03-13T08:11:10.326000Z",
  "updated_at": "2026-05-03T09:01:41.437000Z",
  "languages": ["es"],
  "visibility": "public",
  "lock_visibility": false,
  "dmca_taken_down": false,
  "default_text": "Hermanos míos, recordemos las palabras del Señor...",
  "quality": null,
  "like_count": 4344,
  "mark_count": 4409,
  "shared_count": 590,
  "task_count": 708461,
  "unliked": false,
  "liked": false,
  "marked": false,
  "author": {
    "_id": "1b82fb6a329c4462b67aa9ee0a42046f",
    "nickname": "Fernando Caicedo",
    "avatar": "avatars/1b82fb6a329c4462b67aa9ee0a42046f.jpg"
  }
}
```

拿到的 `_id` 直接喂给 [Fish TTS](https://platform.acedata.cloud/documents/fish-tts) 的 `reference_id` 即可合成相同音色的语音：

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

## 与列表接口的差异

| 字段                                              | `GET /fish/model`（列表） | `GET /fish/model/{id}`（详情） |
| ------------------------------------------------- | ------------------------- | ------------------------------- |
| `samples[].audio`                                 | 短期 R2 缓存 URL          | 现签的 R2 直链（含 query 签名） |
| `unliked` / `liked` / `marked` / `dmca_taken_down` | 同样存在                  | 同样存在                        |
| `default_text` / `lock_visibility`                | 同样存在                  | 同样存在                        |

如果只是要试听一下，列表接口里的 `samples[].audio` 已经够用；要更稳定的下载链接，建议改用本接口。

## 响应字段（节选）

| 字段          | 类型     | 说明                                                                |
| ------------- | -------- | ------------------------------------------------------------------- |
| `_id`         | string   | 音色 ID（用于 `/fish/tts` 的 `reference_id`）。                     |
| `type`        | string   | 模型类型，通常为 `tts`。                                           |
| `title`       | string   | 音色名称。                                                          |
| `description` | string   | 长描述。                                                            |
| `state`       | string   | 训练状态：`trained` 表示可用，`training` 表示还在训练。              |
| `tags`        | string[] | 公共库标签。                                                        |
| `samples`     | object[] | 预置样本，含 `title`、`text`、`task_id`、`audio` 直链。              |
| `languages`   | string[] | 音色擅长的语种代码。                                                |
| `visibility`  | string   | `public` 或 `private`。                                             |
| `like_count`  | integer  | 公共库点赞数。                                                      |
| `task_count`  | integer  | 历史合成次数（可用于人气排序参考）。                                |
| `author`      | object   | 上游作者信息：`_id` / `nickname` / `avatar`。                       |
| `created_at`  | string   | ISO 8601 创建时间。                                                  |
| `updated_at`  | string   | ISO 8601 最近更新时间。                                              |

## 计费说明

本接口不计费——按 ID 查询单个音色详情是免费操作。创建音色（[Fish Model Create](https://platform.acedata.cloud/documents/fish-model)）同样免费，费用仅在调用 [Fish TTS](https://platform.acedata.cloud/documents/fish-tts) 合成语音时按用量产生。

## 错误处理

- `400 token_mismatched`：路径中的 `id` 不是合法格式，或上游报「Model not found」。
- `401 invalid_token`：鉴权 token 不存在或无效。
- `404 not_found`：指定 `_id` 在 Fish 上游不可见（音色被删除、私密、或属于其他账号）。
- `429 too_many_requests`：触发账号速率限制。
- `500 api_error`：服务器内部错误。

实际请求一个不存在的 ID 时上游会直接返回 `400 Model not found`（实测）：

```shell
curl 'https://api.acedata.cloud/fish/model/test123' \
  -H 'authorization: Bearer {token}'
```

返回：

```json
{ "status": 400, "message": "Model not found" }
```

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

## 结论

知道音色 `_id` 时直接用本接口拿完整 ModelEntity，最常见的用法是：(1) 试听 `samples[].audio`，(2) 把 `_id` 喂给 `/fish/tts` 的 `reference_id` 完成合成。如果只有标题或标签，请先用 [Fish Model Query](https://platform.acedata.cloud/documents/fish-model-query) 检索。
