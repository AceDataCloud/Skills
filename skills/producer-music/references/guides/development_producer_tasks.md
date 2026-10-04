# Producer Tasks API 的对接和使用

Producer Tasks API 的主要功能是通过输入 Producer Audios Generation API 生成的任务ID来查询该任务的执行情况。


本文档将详细介绍  Producer Tasks API  的对接说明，帮助您轻松集成并充分利用该 API 的强大功能。通过  Producer Tasks API ，您可以轻松实现查询  Producer Audios Generation API 的任务执行情况。

## 申请流程

要使用 Producer Audios Generation API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Producer Audios Generation API →](https://platform.acedata.cloud/documents/producer-audios)

## 请求示例
Producer Tasks API 可以用于查询 Producer Audios Generation API 的结果。关于怎样使用 Producer Audios Generation API，请参考文档 [Producer Audios Generation API ](https://platform.acedata.cloud/documents/producer-audios-integration)。

我们以 Producer Audios Generation API 服务返回的任务ID一个为例，演示如何使用该 API。假设我们有一个任务ID：1a6ac2ad-10f2-4e2b-b500-66ec27fe82ad，接下来演示如何通过传入一个任务ID来。

### 任务示例图

<p><img src="https://cdn.acedata.cloud/om6p6g.png" width="500" class="m-auto"></p>

### 设置请求头和请求体

**Request Headers** 包括：

- `accept`：指定接收 JSON 格式的响应结果，这里填写为 `application/json`。
- `authorization`：调用 API 的密钥，申请之后可以直接下拉选择。

**Request Body** 包括：

- `id`：上传的任务ID。
- `action`：对任务的操作方式。

设置如下图所示：

<p><img src="https://cdn.acedata.cloud/bfe4ww.png" width="500" class="m-auto"></p>

### 代码示例

可以发现，在页面右侧已经自动生成了各种语言的代码，如图所示：

<p><img src="https://cdn.acedata.cloud/u4pb2f.png" width="500" class="m-auto"></p>

部分代码示例如下：

#### CURL

```bash
curl -X POST 'https://api.acedata.cloud/producer/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "id": "1a6ac2ad-10f2-4e2b-b500-66ec27fe82ad",
  "action": "retrieve"
}'
```

### 响应示例

请求成功后，API 将返回此处任务的详情信息。例如：

```json
{
  "_id": "69541b81ff2676299ccc3b29",
  "id": "1a6ac2ad-10f2-4e2b-b500-66ec27fe82ad",
  "api_id": "01d96900-9f8c-41d7-814c-95c7a885ba61",
  "application_id": "920ba772-867a-48ae-8efa-9b9f94136199",
  "created_at": 1767119745.524,
  "started_at": 1767119745.584,
  "finished_at": 1767119785.589,
  "elapsed": 40.005,
  "credential_id": "eeae817d-d6ff-493e-8f88-6c62391da7c6",
  "request": {
    "action": "generate",
    "model": "FUZZ-2.0 Pro",
    "instrumental": false,
    "lyric": "[Verse]\nWoke up with the sun in my eyes\nNo clouds above just blue in the skies\nShoes on my feet I’m ready to run\nEvery step feels like a loaded gun\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Verse 2]\nDancing through the city streets\nA rhythm pounding in my heartbeat\nStrangers smile it’s catching on\nThis world’s a stage we’re all a song\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Bridge]\nThrow your worries out the door\nLet them sink to the ocean floor\nWe’re alive and it’s enough\nLife is messy but it’s love\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high",
    "custom": true,
    "callback_url": "https://webhook.site/0d73431d-f833-4be4-9276-b6e1690d55c1"
  },
  "trace_id": "1da03537-4eb8-410d-b849-43f03085a3bb",
  "type": "audios",
  "user_id": "ad7afe47-cea9-4cda-980f-2ad8810e51cf",
  "response": {
    "task_id": "1a6ac2ad-10f2-4e2b-b500-66ec27fe82ad",
    "data": [
      {
        "id": "1dd08826-478e-43a6-868f-aff5ababac2c",
        "title": "Woke up with the sun in my eyes",
        "image_url": "https://cdn.acedata.cloud/e724d7f13d.png",
        "lyric": "[Verse]\nWoke up with the sun in my eyes\nNo clouds above just blue in the skies\nShoes on my feet I’m ready to run\nEvery step feels like a loaded gun\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Verse 2]\nDancing through the city streets\nA rhythm pounding in my heartbeat\nStrangers smile it’s catching on\nThis world’s a stage we’re all a song\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Bridge]\nThrow your worries out the door\nLet them sink to the ocean floor\nWe’re alive and it’s enough\nLife is messy but it’s love\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high",
        "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3",
        "video_url": null,
        "image_id": "1dd08826-478e-43a6-868f-aff5ababac2c",
        "topic": null,
        "seed": "1490770667",
        "sound": "",
        "created_at": "2025-12-30T18:36:00.994141Z",
        "model": "FUZZ-2.0 Pro",
        "progress": "100%",
        "state": "succeeded",
        "duration": "135.2330158730159"
      }
    ]
  }
}
```

返回结果一共有多个字段，request 字段就是发起任务时的 request body，同时response 字段是任务完成后返回的response body。字段介绍如下。

- `id`，生成任务的 ID，用于唯一标识此次生成任务。
- `request`，查询任务中的请求信息。
- `response`，查询任务中的返回信息。
- `created_at`，任务创建时间，Unix 时间戳（秒，浮点）。
- `started_at`，任务开始执行时间，Unix 时间戳（秒，浮点）。
- `finished_at`，任务完成时间，Unix 时间戳（秒，浮点）。任务未完成时不返回该字段。
- `elapsed`，任务执行耗时，单位为秒（浮点，保留 3 位小数）。任务未完成时不返回该字段。

## 批量查询操作

这是是针对多个任务ID来进行查询任务详情，与上面不同的是需要将action选中为retrieve_batch

**Request Body** 包括：

- `ids`：上传的任务ID数组。
- `action`：对任务的操作方式。

设置如下图所示：

<p><img src="https://cdn.acedata.cloud/jlkoma.png" width="500" class="m-auto"></p>

### 代码示例

可以发现，在页面右侧已经自动生成了各种语言的代码，如图所示：

<p><img src="https://cdn.acedata.cloud/emw66n.png" width="500" class="m-auto"></p>

部分代码示例如下：

#### CURL

```bash
curl -X POST 'https://api.acedata.cloud/producer/tasks' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "ids": ["1a6ac2ad-10f2-4e2b-b500-66ec27fe82ad","1a6ac2ad-10f2-4e2b-b500-66ec27fe82ad"],
  "action": "retrieve_batch"
}'
```

### 响应示例

请求成功后，API 将返回此次所有批量任务的具体详情信息。例如：

```json
{
  "items": [
    {
      "_id": "69541b81ff2676299ccc3b29",
      "id": "1a6ac2ad-10f2-4e2b-b500-66ec27fe82ad",
      "api_id": "01d96900-9f8c-41d7-814c-95c7a885ba61",
      "application_id": "920ba772-867a-48ae-8efa-9b9f94136199",
      "created_at": 1767119745.524,
      "started_at": 1767119745.584,
      "finished_at": 1767119785.589,
      "elapsed": 40.005,
      "credential_id": "eeae817d-d6ff-493e-8f88-6c62391da7c6",
      "request": {
        "action": "generate",
        "model": "FUZZ-2.0 Pro",
        "instrumental": false,
        "lyric": "[Verse]\nWoke up with the sun in my eyes\nNo clouds above just blue in the skies\nShoes on my feet I’m ready to run\nEvery step feels like a loaded gun\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Verse 2]\nDancing through the city streets\nA rhythm pounding in my heartbeat\nStrangers smile it’s catching on\nThis world’s a stage we’re all a song\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Bridge]\nThrow your worries out the door\nLet them sink to the ocean floor\nWe’re alive and it’s enough\nLife is messy but it’s love\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high",
        "custom": true,
        "callback_url": "https://webhook.site/0d73431d-f833-4be4-9276-b6e1690d55c1"
      },
      "trace_id": "1da03537-4eb8-410d-b849-43f03085a3bb",
      "type": "audios",
      "user_id": "ad7afe47-cea9-4cda-980f-2ad8810e51cf",
      "response": {
        "task_id": "1a6ac2ad-10f2-4e2b-b500-66ec27fe82ad",
        "data": [
          {
            "id": "1dd08826-478e-43a6-868f-aff5ababac2c",
            "title": "Woke up with the sun in my eyes",
            "image_url": "https://cdn.acedata.cloud/e724d7f13d.png",
            "lyric": "[Verse]\nWoke up with the sun in my eyes\nNo clouds above just blue in the skies\nShoes on my feet I’m ready to run\nEvery step feels like a loaded gun\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Verse 2]\nDancing through the city streets\nA rhythm pounding in my heartbeat\nStrangers smile it’s catching on\nThis world’s a stage we’re all a song\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Bridge]\nThrow your worries out the door\nLet them sink to the ocean floor\nWe’re alive and it’s enough\nLife is messy but it’s love\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high",
            "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3",
            "video_url": null,
            "image_id": "1dd08826-478e-43a6-868f-aff5ababac2c",
            "topic": null,
            "seed": "1490770667",
            "sound": "",
            "created_at": "2025-12-30T18:36:00.994141Z",
            "model": "FUZZ-2.0 Pro",
            "progress": "100%",
            "state": "succeeded",
            "duration": "135.2330158730159"
          }
        ]
      }
    },
    {
      "_id": "69541b81ff2676299ccc3b29",
      "id": "1a6ac2ad-10f2-4e2b-b500-66ec27fe82ad",
      "api_id": "01d96900-9f8c-41d7-814c-95c7a885ba61",
      "application_id": "920ba772-867a-48ae-8efa-9b9f94136199",
      "created_at": 1767119745.524,
      "started_at": 1767119745.584,
      "finished_at": 1767119785.589,
      "elapsed": 40.005,
      "credential_id": "eeae817d-d6ff-493e-8f88-6c62391da7c6",
      "request": {
        "action": "generate",
        "model": "FUZZ-2.0 Pro",
        "instrumental": false,
        "lyric": "[Verse]\nWoke up with the sun in my eyes\nNo clouds above just blue in the skies\nShoes on my feet I’m ready to run\nEvery step feels like a loaded gun\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Verse 2]\nDancing through the city streets\nA rhythm pounding in my heartbeat\nStrangers smile it’s catching on\nThis world’s a stage we’re all a song\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Bridge]\nThrow your worries out the door\nLet them sink to the ocean floor\nWe’re alive and it’s enough\nLife is messy but it’s love\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high",
        "custom": true,
        "callback_url": "https://webhook.site/0d73431d-f833-4be4-9276-b6e1690d55c1"
      },
      "trace_id": "1da03537-4eb8-410d-b849-43f03085a3bb",
      "type": "audios",
      "user_id": "ad7afe47-cea9-4cda-980f-2ad8810e51cf",
      "response": {
        "task_id": "1a6ac2ad-10f2-4e2b-b500-66ec27fe82ad",
        "data": [
          {
            "id": "1dd08826-478e-43a6-868f-aff5ababac2c",
            "title": "Woke up with the sun in my eyes",
            "image_url": "https://cdn.acedata.cloud/e724d7f13d.png",
            "lyric": "[Verse]\nWoke up with the sun in my eyes\nNo clouds above just blue in the skies\nShoes on my feet I’m ready to run\nEvery step feels like a loaded gun\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Verse 2]\nDancing through the city streets\nA rhythm pounding in my heartbeat\nStrangers smile it’s catching on\nThis world’s a stage we’re all a song\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Bridge]\nThrow your worries out the door\nLet them sink to the ocean floor\nWe’re alive and it’s enough\nLife is messy but it’s love\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high",
            "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3",
            "video_url": null,
            "image_id": "1dd08826-478e-43a6-868f-aff5ababac2c",
            "topic": null,
            "seed": "1490770667",
            "sound": "",
            "created_at": "2025-12-30T18:36:00.994141Z",
            "model": "FUZZ-2.0 Pro",
            "progress": "100%",
            "state": "succeeded",
            "duration": "135.2330158730159"
          }
        ]
      }
    }
  ],
  "count": 2
}
```

返回结果一共有多个字段，其中items是包含了批量任务的具体详情信息，每个任务的具体信息与上文的字段一样，字段信息如下。

- `items`，批量任务的所有具体详情信息。它是一个数组，每个数组的元素和上文查询单个任务的返回结果格式是一样的。
- `count`，此处批量查询任务的个数。

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

通过本文档，您已经了解了如何使用 Producer Tasks API 进行查询单个或批量任务的所有具体详情信息。希望本文档能帮助您更好地对接和使用该 API。如有任何问题，请随时联系我们的技术支持团队。
