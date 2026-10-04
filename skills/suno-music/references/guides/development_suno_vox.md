# Suno Vox API 对接说明

SUNO 允许我们创建新版的Persona-v2-vox 版:歌手风格，与旧版本不同的需要先获取`vox_audio_id`。本文档讲解创建新版Persona-v2-vox的 对接方法。


首选需要该 API获取`vox_audio_id`参数值， 该API可以输入多个个输入参数，比如 `audio_id`、`vocal_start`、`vocal_end`，它是参考歌曲ID以及选定的时间范围。

这里我们输入的 `audio_id` 是 `42599b24-fb14-4cd3-a444-e15ffde3661b`。

```python
import requests

url = "https://api.acedata.cloud/suno/vox"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "audio_id": "42599b24-fb14-4cd3-a444-e15ffde3661b",
    "vocal_end": 30,
    "vocal_start": 20
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

结果如下：

```json
{
  "success": true,
  "task_id": "9d5ce870-18e3-4c17-a1d9-7ef5a07918e9",
  "trace_id": "c31b50cd-0dbe-4e53-a7a5-83965dc5ad6b",
  "data": {
    "id": "24f0827e-5847-4011-b9b7-fc0b62032b65",
    "source_clip_id": "42599b24-fb14-4cd3-a444-e15ffde3661b",
    "status": "complete",
    "vocal_audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3",
    "vocal_end_s": 30,
    "vocal_start_s": 20,
    "wave_response": {
      "waveform_aggregates": [
        {
          "data": [
            [
              -4,
              4,
              -50,
              73,
              -2517,
              2887,

              294
            ],
            [
              -5,
              4,
              296
            ]
          ],
          "mip_map_level": 11
        },

        {
          "data": [
            [
              -19576,
              20406,
              -16717,
              16980,
              -18926,
              20807,
              -20029,
              20103,
              -16437,
              20899
            ],
            [
              -19578,
              20406,
              -16720,
              16980,
              -18825,
              20051,
              -20029,
              20103,
              -16453,
              20903
            ]
          ],
          "mip_map_level": 20
        }
      ]
    }
  }
}
```


可以看到，`data` 的 `id` 字段就是我们想要的`vox_audio_id`，然后我们去[Persona API](https://platform.acedata.cloud/documents/suno-persona)创建新版的Persona-v2-vox:歌手风格，具体输入如下所示：

```python
import requests

url = "https://api.acedata.cloud/suno/persona"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "name": "test",
    "audio_id": "42599b24-fb14-4cd3-a444-e15ffde3661b",
    "vocal_end": 30,
    "vocal_start": 20,
    "vox_audio_id": "24f0827e-5847-4011-b9b7-fc0b62032b65"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

调用后得到如下结果：

```json
{
  "success": true,
  "task_id": "e04b06a1-ff61-48e2-9fcc-15284bd18481",
  "data": {
    "persona_id": "49bef16d-6a09-49d1-8c24-a81663698b98"
  }
}
```

然后我们可以根据上面的`persona_id`值进行新版的Persona-v2-vox:歌手风格进行创作，具体的创作方法和[Suno 歌曲生成 API 对接说明](https://platform.acedata.cloud/documents/suno-audios-integration#%E8%87%AA%E5%AE%9A%E4%B9%89%E6%AD%8C%E6%89%8B%E9%A3%8E%E6%A0%BC%E7%94%9F%E6%88%90%E5%8A%9F%E8%83%BD)一致，最后我们就可以通过Suno Vox API来实现新版的Persona-v2-vox:歌手风格进行创作歌曲。
