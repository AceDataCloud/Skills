# Suno 自定义歌手风格 API 对接说明

SUNO 允许我们对已经生成后的歌曲设定歌手风格，然后根据它进行二次创作，本文档讲解相关 API 的对接方法。

该 API 只有三个输入参数，首先 `audio_id`，它是一个已经在官方生成成功后的歌曲ID，其次 `name` 、`description` 它是对歌手风格的一种名称和描述。

这里我们输入的 `audio_id` 是 `https://cdn.acedata.cloud/2qhzs3.png`，这个可以参考[Suno Audios Generation API](https://platform.acedata.cloud/documents/suno-audios) 来进行自定义歌曲生成，最后可以得到`audio_id`。

```bash
curl -X POST 'https://api.acedata.cloud/suno/persona' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "name": "test",
  "audio_id": "81745564-60e7-4ad4-85a9-6f42f0f4f3b3",
  "description": "test"
}'
```

结果如下：

```
{
  "success": true,
  "task_id": "8e808558-f056-456f-91d6-b97fd94eb3be",
  "data": {
    "persona_id": "dae4ae5d-2b51-4af1-b286-1a4473ef4dba"
  }
}
```

可以看到，`data` 的 `persona_id` 字段就是生成后的歌手风格 ID。

有了歌手风格 ID 之后，我们便可以使用 [Suno Audios Generation API](https://platform.acedata.cloud/documents/suno-audios) 来进行自定义歌曲生成了，比如说 `action` 传入 `artist_consistency`，同时 `audio_id` 传入上传的歌曲 ID，还需要上传参数 `persona_id`，这个值是上面返回的歌手风格 ID， 就可以根据参考的歌手风格生成新的歌曲了。
