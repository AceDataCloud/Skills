# Suno 声音克隆 API 对接说明

SUNO 允许我们通过任意音频文件创建自定义声音角色，实现声音克隆用于音乐生成。与已有的 Persona API（使用 Suno 生成的 `audio_id`）不同，该 API 接受一个公开可访问的 `audio_url`，即你自己的人声录音。本文档讲解声音克隆 API 的对接方法。

## 第一步：创建声音角色

该 API 有三个输入参数：`audio_url`（必填），为一个公开可访问的 MP3 或 WAV 格式音频文件 URL，其中包含单人清晰人声；`name` 和 `description`（可选），为声音角色的名称和描述。

> **音频文件要求**
>
> - 音频格式需为 `WAV` 或 `MP3`
> - 音频时长需在 `10~240 秒` 之间，推荐使用 `30~60 秒` 的干净单人干声素材
> - 音频中应包含**清晰、可辨识的单人讲话或演唱人声**
> - 请务必避免**背景噪音、伴奏、回声、混响**；带伴奏的完整歌曲通常无法通过声纹校验
> - 不要包含**多位说话人**或**多重人声**
> - 音量过低、语音不清晰、噪声过重的素材，可能导致**克隆失败**或**生成效果较差**
>
> **使用限制说明**
>
> - 通过上传音频创建的声音角色为**私有资源**
> - 该声音角色**不支持跨账号复用**
> - 建议在创建成功后尽快使用，长时间不使用可能出现**失效或不可用**
> - 返回的 `name` 由系统自动生成，请以返回的 `persona_id` 为准

> **调用失败时请先重试**
>
> 声音克隆为算力密集型任务，即使素材完全合规也存在一定概率的偶发失败，常见返回如
> `voices_sound_different`（声纹校验未通过）等。**这类失败与音频质量无关，使用同一素材重试通常即可成功**，
> 建议在集成时对失败结果实现 1~2 次自动重试。失败的请求不会计费。

```bash
curl -X POST 'https://api.acedata.cloud/suno/voices' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "audio_url": "https://cdn.acedata.cloud/suno_demo.mp3",
  "name": "My Voice",
  "description": "单人清晰人声示例"
}'
```

> 上述 `https://cdn.acedata.cloud/suno_demo.mp3` 为可直接调用的示例素材（MP3，41 秒，单人干声）。
> 如需 `WAV` 格式示例，可使用
> `https://cdn.acedata.cloud/uploads/82d23b97-ec1c-4b41-91b8-989fc51f8765`（WAV，41 秒，单声道 44.1kHz）。

结果如下：

```json
{
  "success": true,
  "task_id": "0fa609a6-c8d9-4bb5-8574-e4c93bb55d02",
  "data": {
    "persona_id": "1ab79a71-a229-4350-8f02-402ff02eac16",
    "name": "VOICE_20260803037676",
    "is_public": false
  }
}
```

可以看到，`data` 的 `persona_id` 字段就是创建的声音角色 ID。`is_public` 字段始终为 `false`，因为通过上传音频创建的声音角色是私有的。注意返回的 `name` 为系统自动生成，后续请使用 `persona_id` 引用该声音角色。

## 第二步：使用声音角色生成音乐

有了声音角色 ID 之后，我们便可以使用 [Suno Audios Generation API](https://platform.acedata.cloud/documents/suno-audios) 来进行音乐生成了。将 `action` 设为 `generate`，并将 `persona_id` 设为上面返回的声音角色 ID，生成的歌曲将使用克隆的声音进行演唱。

> **注意：** 声音克隆仅支持 `chirp-v4-5` 及以上模型（如 `chirp-v4-5`、`chirp-v5`、`chirp-v5-5`），不支持 `chirp-v4`。

```bash
curl -X POST 'https://api.acedata.cloud/suno/audios' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "action": "generate",
  "model": "chirp-v5-5",
  "prompt": "A warm synth-pop song about city nights",
  "persona_id": "1ab79a71-a229-4350-8f02-402ff02eac16"
}'
```

结果如下：

```json
{
  "success": true,
  "task_id": "53d8a334-a972-43c5-895e-60c4454e88d5",
  "data": [
    {
      "id": "16463960-077c-4700-bbb3-3c7897b943d3",
      "title": "Soft Neon on My Skin",
      "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3",
      "image_url": "https://cdn.acedata.cloud/e724d7f13d.png",
      "model": "chirp-v5-5",
      "state": "succeeded",
      "prompt": "A warm synth-pop song about city nights",
      "duration": 156.28
    }
  ]
}
```

可以看到，生成的歌曲使用了克隆的声音进行演唱。`persona_id` 也可以与 `cover` 动作配合使用，用克隆的声音翻唱已有歌曲。
