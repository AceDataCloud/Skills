# Fish Model Query API 对接说明

本接口基于 [Fish Audio 官方 Model API](https://docs.fish.audio/resources/api-reference/model)，用于**分页检索 Fish 公共音色库或当前账号下的克隆音色**。地址为 `GET https://api.acedata.cloud/fish/model`。

> 创建音色请参考 [Fish Model Create API](https://platform.acedata.cloud/documents/fish-model)；按 `_id` 查询单个音色详情请参考 [Fish Model Get API](https://platform.acedata.cloud/documents/fish-model-get)。

## 申请流程

要使用 Fish Model API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Fish Model API →](https://platform.acedata.cloud/services/fish)

## 查询参数

| 参数             | 类型    | 默认 | 说明                                                                                  |
| ---------------- | ------- | ---- | ------------------------------------------------------------------------------------- |
| `page_size`      | integer | 10   | 每页条数。                                                                            |
| `page_number`    | integer | 1    | 1 起的页码。                                                                          |
| `title`          | string  | —    | 按标题模糊搜索。                                                                      |
| `tag`            | string  | —    | 按单个标签过滤。                                                                      |
| `self`           | boolean | —    | `true` 时仅返回当前账号创建的音色，无需任何额外条件。                                  |
| `author_id`      | string  | —    | 按上游用户 `_id` 过滤。                                                               |
| `language`       | string  | —    | 按音色语种过滤，如 `en`、`zh`、`es`。                                                  |
| `title_language` | string  | —    | 按标题语种过滤。                                                                      |
| `sort_by`        | string  | —    | 排序字段，与上游一致，如 `created_at`、`task_count`。                                  |

> 参数命名与上游 `GET https://api.fish.audio/model` 完全一致，详见 [Fish 官方文档](https://docs.fish.audio/resources/api-reference/model)。

## 示例 1：默认翻页（按 `page_size`）

```shell
curl -G 'https://api.acedata.cloud/fish/model' \
  -H 'authorization: Bearer {token}' \
  --data-urlencode 'page_size=2'
```

返回（实测，公共库总量约 180 万条；为可读性下例省略了部分长字段）：

```json
{
  "total": 1829200,
  "items": [
    {
      "_id": "8d2c17a9b26d4d83888ea67a1ee565b2",
      "type": "tts",
      "title": "Valentino Narración Biblica Fer",
      "description": "A mature and authoritative male voice with a calm, spiritual tone...",
      "cover_image": "coverimage/8d2c17a9b26d4d83888ea67a1ee565b2",
      "train_mode": "fast",
      "state": "trained",
      "tags": ["male", "old", "narration", "calm", "Spanish"],
      "samples": [
        {
          "title": "Default Sample",
          "text": "Hermanos míos, recordemos las palabras del Señor...",
          "task_id": "59ce7df6935c42249759327ddf70f37b",
          "audio": "https://platform.r2.fish.audio/task/59ce7df6935c42249759327ddf70f37b.mp3"
        }
      ],
      "languages": ["es"],
      "visibility": "public",
      "like_count": 4344,
      "task_count": 708461,
      "author": {
        "_id": "1b82fb6a329c4462b67aa9ee0a42046f",
        "nickname": "Fernando Caicedo"
      }
    },
    {
      "_id": "90e65eaaf50e4470b8e6d43ee6afd7d5",
      "type": "tts",
      "title": "Super Smash Bros. 4/Ultimate Announcer",
      "tags": ["male", "old", "announcer", "gaming", "cinematic"],
      "languages": ["en"],
      "visibility": "public"
    }
  ],
  "has_more": null
}
```

## 示例 2：按标题模糊搜索（`title`）

```shell
curl -G 'https://api.acedata.cloud/fish/model' \
  -H 'authorization: Bearer {token}' \
  --data-urlencode 'title=narration' \
  --data-urlencode 'page_size=2'
```

返回（实测）：

```json
{
  "total": 161,
  "items": [
    {
      "_id": "fb8fe4a94658429d9be70efd4eec35a2",
      "type": "tts",
      "title": "Miles Morales ( Narration Paw )",
      "tags": ["male", "middle-aged", "entertainment", "storytelling", "Children's Content"],
      "languages": ["en"],
      "visibility": "public",
      "task_count": 770
    },
    {
      "_id": "76b55591c758444cb95253708696dfad",
      "type": "tts",
      "title": "Joe NARRATION",
      "tags": ["male", "middle-aged", "narration", "deep", "raspy"],
      "languages": ["en"],
      "visibility": "public"
    }
  ],
  "has_more": null
}
```

注意 `title` 是「全局模糊匹配」，会同时命中 Fish 公共库的所有音色（不仅是自己的）。

## 示例 3：只列出自己创建的音色（`self=true`）

```shell
curl -G 'https://api.acedata.cloud/fish/model' \
  -H 'authorization: Bearer {token}' \
  --data-urlencode 'self=true' \
  --data-urlencode 'page_size=5'
```

返回（实测，当前账号下只有 1 个音色）：

```json
{
  "total": 1,
  "items": [
    {
      "_id": "e5c6db52c3ed417f9cb2e5a33fb04667",
      "type": "tts",
      "title": "copilot-smoke-test",
      "description": "smoke test from api.acedata.cloud",
      "state": "trained",
      "languages": ["zh"],
      "visibility": "public",
      "samples": [
        {
          "title": "Default Sample",
          "text": "师父，[语气坚定]我真的受够了这山上的清冷日子！...",
          "task_id": "6a1bf398dfae49dca0e23159214342a0",
          "audio": "https://platform.r2.fish.audio/task/6a1bf398dfae49dca0e23159214342a0.mp3"
        }
      ],
      "created_at": "2026-05-10T03:52:55.601000Z",
      "author": {
        "_id": "780f2b2f862d41a08c0507bbbda77eb6",
        "nickname": "Penny Conrad"
      }
    }
  ],
  "has_more": null
}
```

`self=true` 等价于在过滤里限定 `author_id == 当前账号上游 ID`，是常用的「我自己的音色列表」入口。

## 示例 4：按语种 + 标签过滤

```shell
curl -G 'https://api.acedata.cloud/fish/model' \
  -H 'authorization: Bearer {token}' \
  --data-urlencode 'language=zh' \
  --data-urlencode 'tag=narration' \
  --data-urlencode 'page_size=5'
```

> 上游对未在标签字典里的 `tag` 也会返回结果，但匹配相对宽松；如果命中数为 0，建议改用 `title` 模糊匹配。

## 响应字段

`items[]` 中的每一项是一个完整 ModelEntity 对象，常用字段：

| 字段           | 类型     | 说明                                                             |
| -------------- | -------- | ---------------------------------------------------------------- |
| `_id`          | string   | 音色 ID，作为 `/fish/tts` 中 `reference_id` 的值。               |
| `type`         | string   | 模型类型，通常为 `tts`。                                         |
| `title`        | string   | 音色名称。                                                       |
| `description`  | string   | 音色描述。                                                       |
| `state`        | string   | 训练状态：`trained` 表示可用。                                   |
| `tags`         | string[] | 公共库标签。                                                     |
| `languages`    | string[] | 音色擅长的语种。                                                 |
| `visibility`   | string   | `public` 或 `private`。                                          |
| `samples`      | object[] | 预置样本（含 `audio` 直链）。                                    |
| `like_count`   | integer  | 公共库点赞数。                                                   |
| `task_count`   | integer  | 历史合成次数。                                                   |
| `author`       | object   | 上游作者信息：`_id` / `nickname` / `avatar`。                    |
| `total`（顶层）| integer  | 满足条件的总条数。                                               |
| `has_more`     | boolean? | 上游分页指示，可能为 `null`。建议改用 `total / page_size` 计算总页数。 |

## 计费说明

本接口不计费——分页查询音色列表是免费操作。创建音色（[Fish Model Create](https://platform.acedata.cloud/documents/fish-model)）同样免费，费用仅在调用 [Fish TTS](https://platform.acedata.cloud/documents/fish-tts) 合成语音时按用量产生。

## 错误处理

- `400 token_mismatched`：请求参数缺失或不合法。
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

## 结论

要从 Fish 公共库挑选音色喂给 `/fish/tts` 的 `reference_id`，先用本接口配合 `title` / `tag` / `language` 检索，定位到目标 `_id`，再用 [Fish Model Get](https://platform.acedata.cloud/documents/fish-model-get) 拿样本试听。要列出自己创建的音色，传 `self=true` 即可。
