# Suno Tasks API 的对接和使用

Suno Tasks API 的主要功能是通过输入 Suno Audios Generation API 或 Suno Lyrics Generation API 生成的任务ID来查询该任务的执行情况。


本文档将详细介绍  Suno Tasks API  的对接说明，帮助您轻松集成并充分利用该 API 的强大功能。通过  Suno Tasks API ，您可以轻松实现查询 Suno Lyrics Generation API 或 Suno Audios Generation API 的任务执行情况。

## 申请流程

要使用 Suno Audios Generation API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Suno Audios Generation API →](https://platform.acedata.cloud/documents/suno-audios)

## 请求示例
Suno Tasks API 可以用于查询 Suno Audios Generation API 和 Suno Lyrics Generation API 两个 API 的结果。关于怎样使用 Suno Audios Generation API，请参考文档 [Suno Audios Generation API ](https://platform.acedata.cloud/documents/suno-audios-integration)。关于怎样使用 Suno Lyrics Generation API，请参考 [Suno Lyrics Generation API ](https://platform.acedata.cloud/documents/suno-lyrics-generation-integration)。

我们以 Suno Audios Generation API 服务返回的任务ID一个为例，演示如何使用该 API。假设我们有一个任务ID：eae26f89-b64b-404d-a80c-761996660b1c，接下来演示如何通过传入一个任务ID来。

### 任务示例图

<p><img src="https://cdn.acedata.cloud/bc6754.png" width="500" class="m-auto"></p>

### 设置请求头和请求体

**Request Headers** 包括：

- `accept`：指定接收 JSON 格式的响应结果，这里填写为 `application/json`。
- `authorization`：调用 API 的密钥，申请之后可以直接下拉选择。

**Request Body** 包括：

- `id`：上传的任务ID。
- `action`：对任务的操作方式。

设置如下图所示：

<p><img src="https://cdn.acedata.cloud/uo7t6n.png" width="500" class="m-auto"></p>

### 代码示例

可以发现，在页面右侧已经自动生成了各种语言的代码，如图所示：

<p><img src="https://cdn.acedata.cloud/p6vi9o.png" width="500" class="m-auto"></p>

部分代码示例如下：

#### CURL

```bash
curl -X POST 'https://api.acedata.cloud/suno/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "id": "eae26f89-b64b-404d-a80c-761996660b1c",
  "action": "retrieve"
}'
```

#### Python

```python
import requests

url = "https://api.acedata.cloud/suno/tasks"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "id": "eae26f89-b64b-404d-a80c-761996660b1c",
    "action": "retrieve"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

### 响应示例

请求成功后，API 将返回此处歌曲任务的详情信息。例如：

```json
{
  "_id": "66d2add5550a4144a5a88dfe",
  "id": "eae26f89-b64b-404d-a80c-761996660b1c",
  "api_id": "09a26295-5972-4392-9318-dcd9b218f90d",
  "application_id": "ab46a066-ad82-4180-b66b-49dedf8e8a2f",
  "created_at": 1725083093.077,
  "started_at": 1725083093.137,
  "finished_at": 1725083131.537,
  "elapsed": 38.4,
  "credential_id": "66614a7e-e624-494e-87a3-387099b8cbb4",
  "request": {
    "action": "generate",
    "prompt": "A song for Christmas"
  },
  "trace_id": "e13d385a-077e-4376-be01-3465b61ca0fd",
  "user_id": "ad7afe47-cea9-4cda-980f-2ad8810e51cf",
  "response": {
    "success": true,
    "task_id": "eae26f89-b64b-404d-a80c-761996660b1c",
    "data": [
      {
        "id": "b8a4f691-4b14-4120-a7e1-a54a27a0e57e",
        "title": "Holiday Wishes",
        "image_url": "https://cdn.acedata.cloud/e724d7f13d.png",
        "lyric": "[Verse]\nSnow is falling soft and white\nLights are twinkling oh so bright\nKids are laughing full of cheer\nChristmas time is finally here\n[Verse 2]\nBells are ringing in the night\nFireplace is warm with light\nCarols sung by the tree\nEveryone's together we agree\n[Chorus]\nHoliday wishes come true\nTime to share the joy with you\nSmiles and hugs for everyone\nMerry Christmas let's have fun\n[Verse 3]\nGifts are wrapped with loving care\nMagic's floating in the air\nCookies baking in the oven\nChristmas love to be given\n[Chorus]\nHoliday wishes come true\nTime to share the joy with you\nSmiles and hugs for everyone\nMerry Christmas let's have fun\n[Bridge]\nStars are shining in the sky\nHold your loved ones don't ask why\nHeart to heart we're all united\nOn this night we are delighted",
        "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3",
        "video_url": "https://cdn.acedata.cloud/assets/examples/gemini/04a043bd-6b23-4b4e-945c-ce48158c3eee-3a89912507c7.mp4",
        "created_at": "2024-08-31T05:44:54.806Z",
        "model": "chirp-v3.5",
        "prompt": "A song for Christmas",
        "style": "pop",
        "duration": 154.44
      },
      {
        "id": "1a3343b2-2c24-4584-a2a7-687e2f97f09e",
        "title": "Holiday Wishes",
        "image_url": "https://cdn.acedata.cloud/e724d7f13d.png",
        "lyric": "[Verse]\nSnow is falling soft and white\nLights are twinkling oh so bright\nKids are laughing full of cheer\nChristmas time is finally here\n[Verse 2]\nBells are ringing in the night\nFireplace is warm with light\nCarols sung by the tree\nEveryone's together we agree\n[Chorus]\nHoliday wishes come true\nTime to share the joy with you\nSmiles and hugs for everyone\nMerry Christmas let's have fun\n[Verse 3]\nGifts are wrapped with loving care\nMagic's floating in the air\nCookies baking in the oven\nChristmas love to be given\n[Chorus]\nHoliday wishes come true\nTime to share the joy with you\nSmiles and hugs for everyone\nMerry Christmas let's have fun\n[Bridge]\nStars are shining in the sky\nHold your loved ones don't ask why\nHeart to heart we're all united\nOn this night we are delighted",
        "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3",
        "video_url": "https://cdn.acedata.cloud/assets/examples/gemini/04a043bd-6b23-4b4e-945c-ce48158c3eee-3a89912507c7.mp4",
        "created_at": "2024-08-31T05:44:54.806Z",
        "model": "chirp-v3.5",
        "prompt": "A song for Christmas",
        "style": "pop",
        "duration": 147.16
      }
    ]
  }
}
```

返回结果一共有多个字段，request 字段就是发起任务时的 request body，同时response 字段是任务完成后返回的response body。字段介绍如下。

- `id`，生成此歌曲任务的 ID，用于唯一标识此次歌曲生成任务。
- `request`，查询歌曲任务中的请求信息。
- `response`，查询歌曲任务中的返回信息。
- `created_at`，任务创建时间，Unix 时间戳（秒，浮点）。
- `started_at`，任务开始执行时间，Unix 时间戳（秒，浮点）。
- `finished_at`，任务完成时间，Unix 时间戳（秒，浮点）。任务未完成时不返回该字段。
- `elapsed`，任务执行耗时，单位为秒（浮点，保留 3 位小数）。任务未完成时不返回该字段。

## 批量查询操作

这是是针对多个任务ID来进行查询歌曲任务详情，与上面不同的是需要将action选中为retrieve_batch

**Request Body** 包括：

- `ids`：上传的任务ID数组。
- `action`：对任务的操作方式。

设置如下图所示：

<p><img src="https://cdn.acedata.cloud/dqeknz.png" width="500" class="m-auto"></p>

### 代码示例

可以发现，在页面右侧已经自动生成了各种语言的代码，如图所示：

<p><img src="https://cdn.acedata.cloud/1yk792.png" width="500" class="m-auto"></p>

部分代码示例如下：

#### CURL

```bash
curl -X POST 'https://api.acedata.cloud/suno/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "ids": ["eae26f89-b64b-404d-a80c-761996660b1c","0d3ed03b-912b-4f7d-941b-8441323cb77b"],
  "action": "retrieve_batch"
}'
```

#### Python

```python
import requests

url = "https://api.acedata.cloud/suno/tasks"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "ids": ["eae26f89-b64b-404d-a80c-761996660b1c","0d3ed03b-912b-4f7d-941b-8441323cb77b"],
    "action": "retrieve_batch"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

### 响应示例

请求成功后，API 将返回此次所有批量歌曲任务的具体详情信息。例如：

```json
{
  "items": [
    {
      "_id": "66d2add5550a4144a5a88dfe",
      "id": "eae26f89-b64b-404d-a80c-761996660b1c",
      "api_id": "09a26295-5972-4392-9318-dcd9b218f90d",
      "application_id": "ab46a066-ad82-4180-b66b-49dedf8e8a2f",
      "created_at": 1725083093.077,
      "started_at": 1725083093.137,
      "finished_at": 1725083131.537,
      "elapsed": 38.4,
      "credential_id": "66614a7e-e624-494e-87a3-387099b8cbb4",
      "request": {
        "action": "generate",
        "prompt": "A song for Christmas"
      },
      "trace_id": "e13d385a-077e-4376-be01-3465b61ca0fd",
      "user_id": "ad7afe47-cea9-4cda-980f-2ad8810e51cf",
      "response": {
        "success": true,
        "task_id": "eae26f89-b64b-404d-a80c-761996660b1c",
        "data": [
          {
            "id": "b8a4f691-4b14-4120-a7e1-a54a27a0e57e",
            "title": "Holiday Wishes",
            "image_url": "https://cdn.acedata.cloud/e724d7f13d.png",
            "lyric": "[Verse]\nSnow is falling soft and white\nLights are twinkling oh so bright\nKids are laughing full of cheer\nChristmas time is finally here\n[Verse 2]\nBells are ringing in the night\nFireplace is warm with light\nCarols sung by the tree\nEveryone's together we agree\n[Chorus]\nHoliday wishes come true\nTime to share the joy with you\nSmiles and hugs for everyone\nMerry Christmas let's have fun\n[Verse 3]\nGifts are wrapped with loving care\nMagic's floating in the air\nCookies baking in the oven\nChristmas love to be given\n[Chorus]\nHoliday wishes come true\nTime to share the joy with you\nSmiles and hugs for everyone\nMerry Christmas let's have fun\n[Bridge]\nStars are shining in the sky\nHold your loved ones don't ask why\nHeart to heart we're all united\nOn this night we are delighted",
            "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3",
            "video_url": "https://cdn.acedata.cloud/assets/examples/gemini/04a043bd-6b23-4b4e-945c-ce48158c3eee-3a89912507c7.mp4",
            "created_at": "2024-08-31T05:44:54.806Z",
            "model": "chirp-v3.5",
            "prompt": "A song for Christmas",
            "style": "pop",
            "duration": 154.44
          },
          {
            "id": "1a3343b2-2c24-4584-a2a7-687e2f97f09e",
            "title": "Holiday Wishes",
            "image_url": "https://cdn.acedata.cloud/e724d7f13d.png",
            "lyric": "[Verse]\nSnow is falling soft and white\nLights are twinkling oh so bright\nKids are laughing full of cheer\nChristmas time is finally here\n[Verse 2]\nBells are ringing in the night\nFireplace is warm with light\nCarols sung by the tree\nEveryone's together we agree\n[Chorus]\nHoliday wishes come true\nTime to share the joy with you\nSmiles and hugs for everyone\nMerry Christmas let's have fun\n[Verse 3]\nGifts are wrapped with loving care\nMagic's floating in the air\nCookies baking in the oven\nChristmas love to be given\n[Chorus]\nHoliday wishes come true\nTime to share the joy with you\nSmiles and hugs for everyone\nMerry Christmas let's have fun\n[Bridge]\nStars are shining in the sky\nHold your loved ones don't ask why\nHeart to heart we're all united\nOn this night we are delighted",
            "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3",
            "video_url": "https://cdn.acedata.cloud/assets/examples/gemini/04a043bd-6b23-4b4e-945c-ce48158c3eee-3a89912507c7.mp4",
            "created_at": "2024-08-31T05:44:54.806Z",
            "model": "chirp-v3.5",
            "prompt": "A song for Christmas",
            "style": "pop",
            "duration": 147.16
          }
        ]
      }
    },
    {
      "_id": "66d2b03c550a4144a5a8d93d",
      "id": "0d3ed03b-912b-4f7d-941b-8441323cb77b",
      "api_id": "09a26295-5972-4392-9318-dcd9b218f90d",
      "application_id": "ab46a066-ad82-4180-b66b-49dedf8e8a2f",
      "created_at": 1725083708.53,
      "started_at": 1725083708.59,
      "finished_at": 1725083746.99,
      "elapsed": 38.4,
      "credential_id": "66614a7e-e624-494e-87a3-387099b8cbb4",
      "request": {
        "action": "generate",
        "prompt": "la la la"
      },
      "trace_id": "29ebb919-1126-4156-86cc-4ad899432a8c",
      "user_id": "ad7afe47-cea9-4cda-980f-2ad8810e51cf",
      "response": {
        "success": true,
        "task_id": "0d3ed03b-912b-4f7d-941b-8441323cb77b",
        "data": [
          {
            "id": "b4f498b2-e86f-4172-926a-39da9df84dd3",
            "title": "La La La",
            "image_url": "https://cdn.acedata.cloud/e724d7f13d.png",
            "lyric": "[Verse]\nMi vekiĝas ĉiumatene\nRigardas tra la fenestro\nSunbrilo brilanta hela\nKomenco de nova tago\n[Verse 2]\nLa birdoj kantas ĝoje\nMi dancas en la ĝardeno\nĈirkaŭas min floroj belaj\nĈiu momento ĉi estas mia\n[Chorus]\nLa la la la la la\nKantu kun mi\nNe haltu\nLa la la la la la\nĜoju ĝuante la vivon\n[Verse 3]\nLa maro blua kaj vasta\nOndoj tajdas dolĉe\nNi promenas sur plaĝoj\nSendepende de la tempo\n[Bridge]\nKaptu ĉiun horon\nAŭdu miajn kantadojn\nSentu vin libera\nFeliĉa\nDancu laŭ la ritmo nun\n[Chorus]\nLa la la la la la\nKantu kun mi\nNe haltu\nLa la la la la la\nĜoju ĝuante la vivon",
            "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3",
            "video_url": "https://cdn.acedata.cloud/assets/examples/gemini/04a043bd-6b23-4b4e-945c-ce48158c3eee-3a89912507c7.mp4",
            "created_at": "2024-08-31T05:55:09.345Z",
            "model": "chirp-v3.5",
            "prompt": "la la la",
            "style": "pop",
            "duration": 154.32
          },
          {
            "id": "8b44fdf1-3b88-47ac-a351-7c4b4de60549",
            "title": "La La La",
            "image_url": "https://cdn.acedata.cloud/e724d7f13d.png",
            "lyric": "[Verse]\nMi vekiĝas ĉiumatene\nRigardas tra la fenestro\nSunbrilo brilanta hela\nKomenco de nova tago\n[Verse 2]\nLa birdoj kantas ĝoje\nMi dancas en la ĝardeno\nĈirkaŭas min floroj belaj\nĈiu momento ĉi estas mia\n[Chorus]\nLa la la la la la\nKantu kun mi\nNe haltu\nLa la la la la la\nĜoju ĝuante la vivon\n[Verse 3]\nLa maro blua kaj vasta\nOndoj tajdas dolĉe\nNi promenas sur plaĝoj\nSendepende de la tempo\n[Bridge]\nKaptu ĉiun horon\nAŭdu miajn kantadojn\nSentu vin libera\nFeliĉa\nDancu laŭ la ritmo nun\n[Chorus]\nLa la la la la la\nKantu kun mi\nNe haltu\nLa la la la la la\nĜoju ĝuante la vivon",
            "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3",
            "video_url": "https://cdn.acedata.cloud/assets/examples/gemini/04a043bd-6b23-4b4e-945c-ce48158c3eee-3a89912507c7.mp4",
            "created_at": "2024-08-31T05:55:09.345Z",
            "model": "chirp-v3.5",
            "prompt": "la la la",
            "style": "pop",
            "duration": 177.36
          }
        ]
      }
    }
  ],
  "count": 2
}
```

返回结果一共有多个字段，其中items是包含了批量歌曲任务的具体详情信息，每个歌曲任务的具体信息与上文的字段一样，字段信息如下。

- `items`，批量歌曲任务的所有具体详情信息。它是一个数组，每个数组的元素和上文查询单个任务的返回结果格式是一样的。
- `count`，此处批量查询歌曲任务的个数。

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

通过本文档，您已经了解了如何使用 Suno Tasks API 进行查询单个或批量歌曲任务的所有具体详情信息。希望本文档能帮助您更好地对接和使用该 API。如有任何问题，请随时联系我们的技术支持团队。
