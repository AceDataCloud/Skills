# Suno MP4 API 对接说明

SUNO 允许我们对生成的音乐获取官方生成的MP4链接，本文档讲解相关 API 的对接方法。

该 API 只有一个输入参数，就是 `audio_id`，它是官方生成的歌曲ID。

这里我们输入的 `audio_id` 是 `275113ab-fe5c-4bca-a33c-0cca96b39fa6`。

```python
import requests

url = "https://api.acedata.cloud/suno/mp4"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "audio_id": "275113ab-fe5c-4bca-a33c-0cca96b39fa6"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

结果如下：

```
{
  "success": true,
  "task_id": "03ae7cca-c3a2-40a0-98b2-8f33426af438",
  "trace_id": "848d8d5a-d6bb-4e16-bb29-768c22cf1b3b",
  "data": {
    "video_url": "https://cdn.acedata.cloud/assets/examples/gemini/04a043bd-6b23-4b4e-945c-ce48158c3eee-3a89912507c7.mp4"
  }
}
```

可以看到，`data` 的 `video_url` 字段是就是该歌曲所对应的MP4文件链接。
