# Suno Timing API 对接说明

SUNO 允许我们对生成的音乐进行二次创作，获取音乐的歌词、音频时间线，本文档讲解相关 API 的对接方法。

该 API 只有一个输入参数，就是 `audio_id`，它是官方生成的歌曲ID。

这里我们输入的 `audio_id` 是 `ec13e502-d043-4eb2-92ee-e900c6da69d1`。

```python
import requests

url = "https://api.acedata.cloud/suno/timing"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "audio_id": "ec13e502-d043-4eb2-92ee-e900c6da69d1"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

结果节选如下：

```
{
  "success": true,
  "task_id": "ccf72cca-1c82-4580-8575-bb141c7e8e48",
  "trace_id": "d8e0b7c3-6d24-4ed9-98ac-ffe683576a75",
  "data": {
    "aligned_words": [
      {
        "word": "[Verse]\nSnowflakes ",
        "success": true,
        "start_s": 2.63,
        "end_s": 3.43,
        "p_align": 0.531
      },
      {
        "word": "dance ",
        "success": true,
        "start_s": 3.43,
        "end_s": 3.91,
        "p_align": 0.911
      },
      {
        "word": "on ",
        "success": true,
        "start_s": 3.91,
        "end_s": 4.35,
        "p_align": 0.937
      },
      {
        "word": "rooftops ",
        "success": true,
        "start_s": 4.35,
        "end_s": 5.11,
        "p_align": 0.366
      },
      {
        "word": "high\n",
        "success": true,
        "start_s": 5.11,
        "end_s": 6.25,
        "p_align": 0.969
      },
      ...
    ],
    "waveform_data": [0.02138, 0.02193, 0.01806, 0.16597, 0.15168, 0.14243, ...],
    "hoot_cer": 0.35013262599469497,
    "is_streamed": false
  }
}
```

### aligned_words 字段说明

可以看到，`data.aligned_words` 是对象数组，每个对象代表一个带有时间信息的词或短语。

- `word`: 歌词中的实际词或短语
- `success`: 布尔值，表示此词的对齐是否成功
- `start_s`: 词的开始时间
- `end_s`: 词的结束时间
- `p_align`: 对齐的概率或置信度分数，范围为 0 到 1
