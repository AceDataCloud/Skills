# Producer Audios Generation API 对接说明

本文将介绍一种 Producer Audios Generation API 对接说明，它是可以通过输入自定义参数来生成 Producer 官方的音乐。

## 申请流程

要使用 Producer Audios Generation API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Producer Audios Generation API →](https://platform.acedata.cloud/documents/producer-audios)

## 基本使用

想些什么歌曲，可以任意输入一段文字，比如我想生成一个关于圣诞的歌曲，就可以输入 `a song for Christmas`，如图所示：

<p><img src="https://cdn.acedata.cloud/lg9bb0.png" width="600" class="m-auto"></p>

可以看到这里我们设置了 Request Headers，包括：

- `accept`：想要接收怎样格式的响应结果，这里填写为 `application/json`，即 JSON 格式。
- `authorization`：调用 API 的密钥，申请之后可以直接下拉选择。

另外 Request Body 的参数包括：

- `action`：此次音乐生成任务的行为，生成歌曲是 `generate`。
- `model`：创建歌曲采用的模型，目前主要有： **FUZZ-2.0 Pro**、**FUZZ-2.0**、**FUZZ-2.0 Raw**,**FUZZ-1.1 Pro**、**FUZZ-1.0 Pro**、**FUZZ-1.0**、**FUZZ-1.1**、**FUZZ-0.8**。
- `lyric`：歌曲的歌词内容。
- `custom`：是否采用自定义方式生成歌曲。
- `prompt`：灵感模式下的提示词。
- `title`：歌曲标题信息。
- `audio_id`：参考歌曲 ID，用于续写/翻版等操作。
- `continue_at`：从指定秒数开始续写歌曲。
- `replace_section_start`/`replace_section_end`：替换片段的起止时间，单位秒。
- `lyrics_strength`：歌词强度，表示歌词在音频生成中的影响程度，可选0-1之间，默认0.7。
- `sound_strength`：音频提示词强度，可选0.2-1之间，默认0.7。
- `cover_strength`：翻唱强度 0.2-1之间，默认1。
- `weirdness`：风格奇特度，可选 0-1之间，默认0.5
- `callback_url`：需要回调结果的 URL。
- `async`：可选，设为 `true` 时接口立即返回 `task_id`，无需提供 `callback_url`，随后通过对应的任务查询接口轮询获取结果。
- `instrumental`：是否为无歌词模式。

选择之后，可以发现右侧也生成了对应代码，如图所示：

<p><img src="https://cdn.acedata.cloud/0217zy.png" width="500" class="m-auto"></p>

点击「Try」按钮即可进行测试，如上图所示，这里我们就得到了如下结果：

```json
{
  "success": true,
  "task_id": "82fd443a-903a-4f18-8028-12d2f8a0a4be",
  "trace_id": "d85839fa-0bb1-42da-a9fc-cd582c29027d",
  "data": [
    {
      "id": "6c947f13-a3c5-4b9c-8609-5639c37cdc2d",
      "title": "Untitled",
      "image_url": "https://cdn.acedata.cloud/e724d7f13d.png",
      "lyric": "[Instrumental]",
      "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3",
      "video_url": null,
      "image_id": "6c947f13-a3c5-4b9c-8609-5639c37cdc2d",
      "topic": null,
      "seed": "2450882164",
      "sound": "A song for Christmas",
      "created_at": "2025-12-30T17:18:23.232911Z",
      "model": "FUZZ-2.0 Pro",
      "progress": "100%",
      "state": "succeeded",
      "duration": "181.3014058956916"
    }
  ]
}
```

返回结果一共有多个字段，介绍如下：

- `success`，此时音乐生成任务的状态情况。
  - `data`，此次音乐任务的结果
    - `id`，此时音乐生成任务的 ID。
    - `sound`，此时音乐生成任务的提示词。
    -  `seed`，此时音乐生成任务的种子值。
    - `audio_url`，此时音乐生成任务的音频链接。
    - `image_url`，此时音乐生成任务的封面链接。
    - `image_id`，此时音乐生成任务的封面ID。
    - `state`，此时音乐生成任务的状态。
    - `duration`，此时音乐的时长信息。
    - `progress`，此时音乐任务的进度值。
    - `model`，此时音乐生成任务采用的模型信息。
    - `lyric`，此时音乐生成任务的歌词信息。

可以看到我们得到了想生成的音乐信息，我们只需要根据结果中 `data` 的音乐链接地址获取生成的 Producer 音乐即可。

另外如果想生成对应的对接代码，可以直接复制生成，例如 CURL 的代码如下：

```shell
curl -X POST 'https://api.acedata.cloud/producer/audios' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "action": "generate",
  "model": "FUZZ-2.0 Pro",
  "prompt": "A song for Christmas"
}'
```

## 自定义生成

如果想自定义生成歌词，可以输入歌词：

这时候 `lyric` 字段可以传入类似如下内容：

```
[Verse]Woke up with the sun in my eyesNo clouds above just blue in the skiesShoes on my feet I’m ready to runEvery step feels like a loaded gun[Chorus]Happy days are rolling inLet the joy beneath my skinNo more shadows no more liesJust the truth that lifts me high[Verse 2]Dancing through the city streetsA rhythm pounding in my heartbeatStrangers smile it’s catching onThis world’s a stage we’re all a song[Chorus]Happy days are rolling inLet the joy beneath my skinNo more shadows no more liesJust the truth that lifts me high[Bridge]Throw your worries out the doorLet them sink to the ocean floorWe’re alive and it’s enoughLife is messy but it’s love[Chorus]Happy days are rolling inLet the joy beneath my skinNo more shadows no more liesJust the truth that lifts me high
```


接下来我们要根据歌词、标题、风格自定义生成歌曲，就可以指定如下内容：

- lyric：歌词文本
- custom：填写为 `true`，代表自定义生成，该参数默认为 false，代表使用 `prompt` 生成。
- title：歌曲的标题。

填写样例如下：
<p><img src="https://cdn.acedata.cloud/ruovz5.png" width="500" class="m-auto"></p>

填写完毕之后自动生成了代码如下：

<p><img src="https://cdn.acedata.cloud/seyxxa.png" width="500" class="m-auto"></p>

对应的代码：

```shell
curl -X POST 'https://api.acedata.cloud/producer/audios' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "action": "generate",
  "model": "FUZZ-2.0 Pro",
  "instrumental": false,
  "lyric": "[Verse]\nWoke up with the sun in my eyes\nNo clouds above just blue in the skies\nShoes on my feet I’m ready to run\nEvery step feels like a loaded gun\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Verse 2]\nDancing through the city streets\nA rhythm pounding in my heartbeat\nStrangers smile it’s catching on\nThis world’s a stage we’re all a song\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Bridge]\nThrow your worries out the door\nLet them sink to the ocean floor\nWe’re alive and it’s enough\nLife is messy but it’s love\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high",
  "custom": true
}'
```

测试允许，生成的效果是类似的。

```json
{
  "success": true,
  "task_id": "9f58bbd4-855a-4233-ac45-b63bf9168e02",
  "trace_id": "145ad117-6ce7-42dd-af12-70751c5284fc",
  "data": [
    {
      "id": "38d3b9e2-0dfb-4338-b2a7-15e45656ed32",
      "title": "Woke up with the sun in my eyes",
      "image_url": "https://cdn.acedata.cloud/e724d7f13d.png",
      "lyric": "[Verse]\nWoke up with the sun in my eyes\nNo clouds above just blue in the skies\nShoes on my feet I’m ready to run\nEvery step feels like a loaded gun\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Verse 2]\nDancing through the city streets\nA rhythm pounding in my heartbeat\nStrangers smile it’s catching on\nThis world’s a stage we’re all a song\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Bridge]\nThrow your worries out the door\nLet them sink to the ocean floor\nWe’re alive and it’s enough\nLife is messy but it’s love\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high",
      "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3",
      "video_url": null,
      "image_id": "38d3b9e2-0dfb-4338-b2a7-15e45656ed32",
      "topic": null,
      "seed": "3789209121",
      "sound": "",
      "created_at": "2025-12-30T17:26:46.357055Z",
      "model": "FUZZ-2.0 Pro",
      "progress": "100%",
      "state": "succeeded",
      "duration": "153.80897959183673"
    }
  ]
}
```

## 翻唱歌曲

如果想对已经生成的歌曲进行翻唱操作的操作，可以输入上文生成的歌曲进行翻唱，接下来我们要根据歌词、标题自定义生成歌曲。

如果想对自己上传的歌曲进行继续翻唱的话，可以将参数 `action` 设置为 `upload_cover` ，并且输入需要继续翻唱自定义上传的歌曲 ID，歌曲 ID 的获取是使用 [Producer Upload API](https://platform.acedata.cloud/documents/producer-upload)来获取，如下图所示：

<p><img src="https://cdn.acedata.cloud/z7r5fd.png" width="500" class="m-auto"></p>

就可以指定如下内容：

- action：此次歌曲任务的行为，目前支持：generate、cover、extend、upload_cover、upload_extend、replace_section、swap_vocals、swap_instrumentals、variation，此次翻唱使用`cover`参数。
- lyric：歌词文本
- title：歌曲的标题。
- custom：是否采用自定义模式生成，默认是false。
- audio_id：需要翻唱歌曲的歌曲ID。

填写样例如下：

<p><img src="https://cdn.acedata.cloud/6xl82z.png" width="500" class="m-auto"></p>

填写完毕之后自动生成了代码如下：

<p><img src="https://cdn.acedata.cloud/bxzfrw.png" width="500" class="m-auto"></p>

对应的代码：

```shell
curl -X POST 'https://api.acedata.cloud/producer/audios' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "action": "cover",
  "model": "FUZZ-2.0 Pro",
  "lyric": "[Verse]\nWoke up with the sun in my eyes\nNo clouds above just blue in the skies\nShoes on my feet I’m ready to run\nEvery step feels like a loaded gun\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Verse 2]\nDancing through the city streets\nA rhythm pounding in my heartbeat\nStrangers smile it’s catching on\nThis world’s a stage we’re all a song\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Bridge]\nThrow your worries out the door\nLet them sink to the ocean floor\nWe’re alive and it’s enough\nLife is messy but it’s love\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high",
  "audio_id": "38d3b9e2-0dfb-4338-b2a7-15e45656ed32",
  "instrumental": false,
  "custom": true,
  "title": "Cover"
}'
```

测试允许，生成的效果是类似的。

```json
{
  "success": true,
  "task_id": "dbca350e-6fb9-46ca-9c7e-4c1a9080806f",
  "trace_id": "a39e0fff-ced8-4b31-ae23-aef3badd90fa",
  "data": [
    {
      "id": "e52dd729-38b4-4c2f-9031-59eb7953c593",
      "title": "Cover",
      "image_url": "https://cdn.acedata.cloud/e724d7f13d.png",
      "lyric": "[Verse]\nWoke up with the sun in my eyes\nNo clouds above just blue in the skies\nShoes on my feet I’m ready to run\nEvery step feels like a loaded gun\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Verse 2]\nDancing through the city streets\nA rhythm pounding in my heartbeat\nStrangers smile it’s catching on\nThis world’s a stage we’re all a song\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Bridge]\nThrow your worries out the door\nLet them sink to the ocean floor\nWe’re alive and it’s enough\nLife is messy but it’s love\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high",
      "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3",
      "video_url": null,
      "image_id": "e52dd729-38b4-4c2f-9031-59eb7953c593",
      "topic": null,
      "seed": "358803418",
      "sound": "",
      "created_at": "2025-12-30T17:32:32.951948Z",
      "model": "FUZZ-2.0 Pro",
      "progress": "100%",
      "state": "succeeded",
      "duration": "153.0659410430839"
    }
  ]
}
```

## 续写歌曲

如果想续写歌曲的话，我们需要传入`action`参数值为：`extend`，接下来我们要根据歌词、标题、风格自定义生成歌曲。

如果想对自己上传的歌曲进行继续续写的话，可以将参数 `action` 设置为 `upload_extend` ，并且输入需要继续续写自定义上传的歌曲 ID，歌曲 ID 的获取是使用 [Producer Upload API](https://platform.acedata.cloud/documents/producer-upload)来获取，如下图所示：

<p><img src="https://cdn.acedata.cloud/z7r5fd.png" width="500" class="m-auto"></p>

填写样例如下：

<p><img src="https://cdn.acedata.cloud/r3ux6z.png" width="500" class="m-auto"></p>

填写完毕之后自动生成了代码如下：

<p><img src="https://cdn.acedata.cloud/fsww0u.png" width="500" class="m-auto"></p>

对应的代码：

```shell
curl -X POST 'https://api.acedata.cloud/producer/audios' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "action": "extend",
  "model": "FUZZ-2.0 Pro",
  "instrumental": false,
  "lyric": "[Verse]\nWoke up with the sun in my eyes\nNo clouds above just blue in the skies\nShoes on my feet I’m ready to run\nEvery step feels like a loaded gun\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Verse 2]\nDancing through the city streets\nA rhythm pounding in my heartbeat\nStrangers smile it’s catching on\nThis world’s a stage we’re all a song\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Bridge]\nThrow your worries out the door\nLet them sink to the ocean floor\nWe’re alive and it’s enough\nLife is messy but it’s love\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high",
  "continue_at": 3,
  "audio_id": "38d3b9e2-0dfb-4338-b2a7-15e45656ed32",
  "custom": true,
  "title": "Extend",
  "weirdness": 0.3,
  "sound_strength": 0.3,
  "lyrics_strength": 0.6
}'
```

测试允许，生成的效果是类似的。

```json
{
  "success": true,
  "task_id": "834983cb-d62d-4750-b1aa-461da137e51f",
  "trace_id": "6923eee2-7403-432c-8bd1-e471086385b0",
  "data": [
    {
      "id": "d9ebc609-fb65-4a23-b914-c074747af6a4",
      "title": "Extend",
      "image_url": "https://cdn.acedata.cloud/e724d7f13d.png",
      "lyric": "[Verse]\n[Verse]\nWoke up with the sun in my eyes\nNo clouds above just blue in the skies\nShoes on my feet I’m ready to run\nEvery step feels like a loaded gun\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Verse 2]\nDancing through the city streets\nA rhythm pounding in my heartbeat\nStrangers smile it’s catching on\nThis world’s a stage we’re all a song\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Bridge]\nThrow your worries out the door\nLet them sink to the ocean floor\nWe’re alive and it’s enough\nLife is messy but it’s love\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high",
      "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3",
      "video_url": null,
      "image_id": "d9ebc609-fb65-4a23-b914-c074747af6a4",
      "topic": null,
      "seed": "4294469624",
      "sound": "",
      "created_at": "2025-12-30T17:36:14.520928Z",
      "model": "FUZZ-2.0 Pro",
      "progress": "100%",
      "state": "succeeded",
      "duration": "173.87102040816328"
    }
  ]
}
```

## 音乐变换

如果想根据上一首音乐的seed值生成一首类似效果的新音乐的话，我们需要传入`action`参数值为：`variation`，接下来就可以自定义生成一首类似效果的新音乐。

填写样例如下：

<p><img src="https://cdn.acedata.cloud/bxslxt.png" width="500" class="m-auto"></p>

填写完毕之后自动生成了代码如下：

<p><img src="https://cdn.acedata.cloud/nojowk.png" width="500" class="m-auto"></p>

对应的代码：

```shell
curl -X POST 'https://api.acedata.cloud/producer/audios' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "action": "variation",
  "audio_id": "d9ebc609-fb65-4a23-b914-c074747af6a4",
  "model": "FUZZ-2.0 Pro",
  "instrumental": false,
  "lyric": "[Verse]\nWoke up with the sun in my eyes\nNo clouds above just blue in the skies\nShoes on my feet I’m ready to run\nEvery step feels like a loaded gun\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Verse 2]\nDancing through the city streets\nA rhythm pounding in my heartbeat\nStrangers smile it’s catching on\nThis world’s a stage we’re all a song\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Bridge]\nThrow your worries out the door\nLet them sink to the ocean floor\nWe’re alive and it’s enough\nLife is messy but it’s love\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high",
  "custom": true
}'
```

测试允许，生成的效果是类似的。

```json
{
    "success": true,
    "task_id": "3a74da6d-a37d-4b5d-b116-821f455bce39",
    "trace_id": "8e28cce0-0400-4bfd-83db-6d27f97422c7",
    "data": [
        {
            "id": "c14ca458-cd5a-4700-83d4-5249e15f2707",
            "title": "Woke up with the sun in my eyes",
            "image_url": "https://cdn.acedata.cloud/e724d7f13d.png",
            "lyric": "[Verse]\nWoke up with the sun in my eyes\nNo clouds above just blue in the skies\nShoes on my feet I’m ready to run\nEvery step feels like a loaded gun\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Verse 2]\nDancing through the city streets\nA rhythm pounding in my heartbeat\nStrangers smile it’s catching on\nThis world’s a stage we’re all a song\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Bridge]\nThrow your worries out the door\nLet them sink to the ocean floor\nWe’re alive and it’s enough\nLife is messy but it’s love\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high",
            "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3",
            "video_url": null,
            "image_id": "c14ca458-cd5a-4700-83d4-5249e15f2707",
            "topic": null,
            "seed": "2082104582",
            "sound": "",
            "created_at": "2025-12-30T17:48:40.135187Z",
            "model": "FUZZ-2.0",
            "progress": "100%",
            "state": "succeeded",
            "duration": "173.12798185941043"
        }
    ]
}
```

## 替换片段

如果想对歌曲进行替换片段的话，我们需要传入`action`参数值为：`replace_section`，接下来我们要根据歌词、标题自定义生成歌曲。

如果想对自己上传的歌曲进行继续替换片段的话，可以将参数 `action` 设置为 `upload_replace_section` ，并且输入需要继续续写自定义上传的歌曲 ID，歌曲 ID 的获取是使用 [Producer Upload API](https://platform.acedata.cloud/documents/producer-upload)来获取，如下图所示：

<p><img src="https://cdn.acedata.cloud/z7r5fd.png" width="500" class="m-auto"></p>

填写样例如下：

<p><img src="https://cdn.acedata.cloud/mzo9iw.png" width="500" class="m-auto"></p>

填写完毕之后自动生成了代码如下：

<p><img src="https://cdn.acedata.cloud/877x6c.png" width="500" class="m-auto"></p>

对应的代码：

```shell
curl -X POST 'https://api.acedata.cloud/producer/audios' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "action": "replace_section",
  "model": "FUZZ-2.0 Pro",
  "instrumental": false,
  "lyric": "[Verse]\\nWoke up with the sun in my eyes\\nNo clouds above just blue in the skies\\nShoes on my feet I’m ready to run\\nEvery step feels like a loaded gun\\n[Chorus]\\nHappy days are rolling in\\nLet the joy beneath my skin\\nNo more shadows no more lies\\nJust the truth that lifts me high\\n[Verse 2]\\nDancing through the city streets\\nA rhythm pounding in my heartbeat\\nStrangers smile it’s catching on\\nThis world’s a stage we’re all a song\\n[Chorus]\\nHappy days are rolling in\\nLet the joy beneath my skin\\nNo more shadows no more lies\\nJust the truth that lifts me high\\n[Bridge]\\nThrow your worries out the door\\nLet them sink to the ocean floor\\nWe’re alive and it’s enough\\nLife is messy but it’s love\\n[Chorus]\\nHappy days are rolling in\\nLet the joy beneath my skin\\nNo more shadows no more lies\\nJust the truth that lifts me high",
  "audio_id": "d9ebc609-fb65-4a23-b914-c074747af6a4",
  "replace_section_start": 3,
  "replace_section_end": 70,
  "custom": true
}'
```

测试允许，生成的效果是类似的。

```json
{
    "success": true,
    "task_id": "3cb5ae96-01b0-4a37-afb0-e582608af56f",
    "trace_id": "3ebc6f63-5093-4499-bf9b-95c239e0da4f",
    "data": [
        {
            "id": "a54609c6-13e2-4176-be0f-4d7eebc68e1f",
            "title": "Woke up with the sun in my eyes",
            "image_url": "https://cdn.acedata.cloud/e724d7f13d.png",
            "lyric": "[Verse]\\nWoke up with the sun in my eyes\\nNo clouds above just blue in the skies\\nShoes on my feet I’m ready to run\\nEvery step feels like a loaded gun\\n[Chorus]\\nHappy days are rolling in\\nLet the joy beneath my skin\\nNo more shadows no more lies\\nJust the truth that lifts me high\\n[Verse 2]\\nDancing through the city streets\\nA rhythm pounding in my heartbeat\\nStrangers smile it’s catching on\\nThis world’s a stage we’re all a song\\n[Chorus]\\nHappy days are rolling in\\nLet the joy beneath my skin\\nNo more shadows no more lies\\nJust the truth that lifts me high\\n[Bridge]\\nThrow your worries out the door\\nLet them sink to the ocean floor\\nWe’re alive and it’s enough\\nLife is messy but it’s love\\n[Chorus]\\nHappy days are rolling in\\nLet the joy beneath my skin\\nNo more shadows no more lies\\nJust the truth that lifts me high",
            "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3",
            "video_url": null,
            "image_id": "a54609c6-13e2-4176-be0f-4d7eebc68e1f",
            "topic": null,
            "seed": "14887454",
            "sound": "",
            "created_at": "2025-12-30T18:01:19.907443Z",
            "model": "FUZZ-2.0 Pro",
            "progress": "100%",
            "state": "succeeded",
            "duration": "174.6140589569161"
        }
    ]
}
```

## 伴奏翻版

如果想使用官方的伴奏翻版操作，可以将`action`参数值设为：`swap_instrumentals`，接下来我们要根据歌词、标题自定义生成歌曲。

填写样例如下：

<p><img src="https://cdn.acedata.cloud/7l6976.png" width="500" class="m-auto"></p>

填写完毕之后自动生成了代码如下：

<p><img src="https://cdn.acedata.cloud/pvi2n3.png" width="500" class="m-auto"></p>

对应的代码：

```shell
curl -X POST 'https://api.acedata.cloud/producer/audios' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "action": "swap_instrumentals",
  "model": "FUZZ-2.0 Pro",
  "weirdness": 0.6,
  "prompt": "Happy",
  "audio_id": "d9ebc609-fb65-4a23-b914-c074747af6a4"
}'
```

测试允许，生成的效果是类似的。

```json
{
  "success": true,
  "task_id": "d17d8376-3a58-451d-a976-404719bac11d",
  "trace_id": "ab596807-910a-4e30-bae2-4647895f7d0b",
  "data": [
    {
      "id": "22d7d75c-9e0a-47a8-b22b-eea55eaa0c4b",
      "title": "Extend (Sound swap)",
      "image_url": "https://cdn.acedata.cloud/e724d7f13d.png",
      "lyric": "[Verse]\nWoke up with the sun in my eyes\nNo clouds above just blue in the skies\nShoes on my feet I’m ready to run\nEvery step feels like a loaded gun\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Verse 2]\nDancing through the city streets\nA rhythm pounding in my heartbeat\nStrangers smile it’s catching on\nThis world’s a stage we’re all a song\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Bridge]\nThrow your worries out the door\nLet them sink to the ocean floor\nWe’re alive and it’s enough\nLife is messy but it’s love\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high",
      "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3",
      "video_url": null,
      "image_id": "22d7d75c-9e0a-47a8-b22b-eea55eaa0c4b",
      "topic": null,
      "seed": "2157878068",
      "sound": "Happy",
      "created_at": "2025-12-30T18:09:49.594800Z",
      "model": "FUZZ-2.0 Pro",
      "progress": "100%",
      "state": "succeeded",
      "duration": "172.3849433106576"
    }
  ]
}
```


## 人声翻版

如果想使用官方的人声翻版操作，可以将`action`参数值设为：`swap_vocals`，接下来我们要根据歌词、标题、风格自定义生成歌曲。

填写样例如下：

<p><img src="https://cdn.acedata.cloud/bk9ino.png" width="500" class="m-auto"></p>

填写完毕之后自动生成了代码如下：

<p><img src="https://cdn.acedata.cloud/p5b1vg.png" width="500" class="m-auto"></p>

对应的代码：

```shell
curl -X POST 'https://api.acedata.cloud/producer/audios' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "action": "swap_vocals",
  "model": "FUZZ-2.0 Pro",
  "instrumental": false,
  "lyric": "[Verse]\nWoke up with the sun in my eyes\nNo clouds above just blue in the skies\nShoes on my feet I’m ready to run\nEvery step feels like a loaded gun\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Verse 2]\nDancing through the city streets\nA rhythm pounding in my heartbeat\nStrangers smile it’s catching on\nThis world’s a stage we’re all a song\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Bridge]\nThrow your worries out the door\nLet them sink to the ocean floor\nWe’re alive and it’s enough\nLife is messy but it’s love\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high",
  "weirdness": 0.6,
  "lyrics_strength": 0.8,
  "audio_id": "d9ebc609-fb65-4a23-b914-c074747af6a4",
  "custom": true
}'
```

测试允许，生成的效果是类似的。

```json
{
  "success": true,
  "task_id": "a903ac38-f129-4f85-9181-b1dc5579bd32",
  "trace_id": "9953af52-45e0-4808-bf13-88f0b21262c1",
  "data": [
    {
      "id": "7b2d653b-aaaa-41b0-b737-aee4c4c5693b",
      "title": "Woke up with the sun in my eyes",
      "image_url": "https://cdn.acedata.cloud/e724d7f13d.png",
      "lyric": "[Verse]\nWoke up with the sun in my eyes\nNo clouds above just blue in the skies\nShoes on my feet I’m ready to run\nEvery step feels like a loaded gun\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Verse 2]\nDancing through the city streets\nA rhythm pounding in my heartbeat\nStrangers smile it’s catching on\nThis world’s a stage we’re all a song\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high\n[Bridge]\nThrow your worries out the door\nLet them sink to the ocean floor\nWe’re alive and it’s enough\nLife is messy but it’s love\n[Chorus]\nHappy days are rolling in\nLet the joy beneath my skin\nNo more shadows no more lies\nJust the truth that lifts me high",
      "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3",
      "video_url": null,
      "image_id": "7b2d653b-aaaa-41b0-b737-aee4c4c5693b",
      "topic": null,
      "seed": "2484735707",
      "sound": "",
      "created_at": "2025-12-30T18:13:01.349875Z",
      "model": "FUZZ-2.0 Pro",
      "progress": "100%",
      "state": "succeeded",
      "duration": "173.12798185941043"
    }
  ]
}
```

## 词曲分离

如果想使用官方的词曲分离操作，可以将`action`参数值设为：`stems`，接下来我们要根据歌曲ID进行词曲分离。

填写样例如下：

<p><img src="https://cdn.acedata.cloud/fnpgvc.png" width="500" class="m-auto"></p>

填写完毕之后自动生成了代码如下：

<p><img src="https://cdn.acedata.cloud/oq5iv5.png" width="500" class="m-auto"></p>

对应的代码：

```shell
curl -X POST 'https://api.acedata.cloud/producer/audios' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "action": "stems",
  "audio_id": "a54609c6-13e2-4176-be0f-4d7eebc68e1f"
}'
```

测试允许，生成的效果是类似的。

```json
{
    "success": true,
    "task_id": "561ac695-b4aa-47cf-978d-fb7be2b9ebfc",
    "trace_id": "66d0d397-2987-4bde-84fb-a60d0023b217",
    "data": [
        {
            "title": "Woke up with the sun in my eyes",
            "lyric": "",
            "stems_url": "https://platform.cdn.acedata.cloud/producer/561ac695-b4aa-47cf-978d-fb7be2b9ebfc.zip",
            "model": "",
            "progress": "100%",
            "state": "succeeded"
        }
    ]
}
```

## 异步回调

由于 Producer Audios Generation API 生成的时间有时候会相对较长，如果 API 长时间无响应，HTTP 请求会一直保持连接，导致额外的系统资源消耗，所以本 API 也提供了异步回调的支持。

整体流程是：客户端发起请求的时候，额外指定一个 `callback_url` 字段，客户端发起 API 请求之后，API 会立马返回一个结果，包含一个 `task_id` 的字段信息，代表当前的任务 ID。当任务完成之后，生成任务的结果会通过 POST JSON 的形式发送到客户端指定的 `callback_url`，其中也包括了 `task_id` 字段，这样任务结果就可以通过 ID 关联起来了。

下面我们通过示例来了解下具体怎样操作。

首先，Webhook 回调是一个可以接收 HTTP 请求的服务，开发者应该替换为自己搭建的 HTTP 服务器的 URL。此处为了方便演示，使用一个公开的 Webhook 样例网站 [https://webhook.site/](https://webhook.site/)，打开该网站即可得到一个 Webhook URL，如图所示：

![](https://cdn.acedata.cloud/tbcnai.png)

将此 URL 复制下来，就可以作为 Webhook 来使用，此处的样例为 [https://webhook.site/#!/view/0d73431d-f833-4be4-9276-b6e1690d55c1](https://webhook.site/#!/view/0d73431d-f833-4be4-9276-b6e1690d55c1)。

接下来，我们可以设置字段 `callback_url` 为上述 Webhook URL，同时填入相应的参数，具体的内容如图所示：

<p><img src="https://cdn.acedata.cloud/wuzd4y.png" width="500" class="m-auto"></p>

点击运行，可以发现会立即得到一个结果，如下：

```
{
  "task_id": "1a6ac2ad-10f2-4e2b-b500-66ec27fe82ad"
}
```

稍等片刻，我们可以在 [https://webhook.site/#!/view/0d73431d-f833-4be4-9276-b6e1690d55c1](https://webhook.site/#!/view/0d73431d-f833-4be4-9276-b6e1690d55c1) 上观察到生成任务的结果，如图所示：

![](https://cdn.acedata.cloud/k0kf0y.png)

内容如下：

```json
{
    "success": true,
    "task_id": "1a6ac2ad-10f2-4e2b-b500-66ec27fe82ad",
    "trace_id": "1da03537-4eb8-410d-b849-43f03085a3bb",
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
```

可以看到结果中有一个 `task_id` 字段，其他的字段都和上文类似，通过该字段即可实现任务的关联。

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

通过本文档，您已经了解了如何使用 Producer Audios Generation API 可通过输入提示词来生成音乐。希望本文档能帮助您更好地对接和使用该 API。如有任何问题，请随时联系我们的技术支持团队。
