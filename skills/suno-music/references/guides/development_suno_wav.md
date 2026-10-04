# Suno Wav API 对接说明

SUNO 允许我们获取音乐的wav格式文件，本文档讲解相关 API 的对接方法。

该 API 核心输入参数是 `audio_id`，它是官方生成的歌曲ID；可选还支持 `callback_url` 异步回调地址。

这里我们输入的 `audio_id` 是 `4e43116a-bf09-472c-8e1c-655eabf02682`。

```python
import requests

url = "https://api.acedata.cloud/suno/wav"

headers = {
    "accept": "application/json",
    "authorization": "Bearer YOUR_API_KEY",
    "content-type": "application/json"
}

payload = {
    "audio_id": "4e43116a-bf09-472c-8e1c-655eabf02682"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

结果如下：

```json
{
  "success": true,
  "task_id": "6a5a2099-d6d3-4930-9709-a30ac5dc7de5",
  "trace_id": "3fa70e81-6bb7-4ca8-b718-dd16a4eda7e8",
  "data": [
    {
      "file_url": "https://cdn.acedata.cloud/suno/41572926-1a7a-41bc-adb8-9431e494c144.wav"
    }
  ]
}
```


可以看到，`data` 的 `file_url` 字段是获取的音乐的 wav 格式文件，它是一个可以公开访问的 CDN 地址。

> **关于 WAV 链接的持久化**
>
> 平台会在返回前优先将终态 WAV 文件持久化到 Ace Data Cloud CDN。上方 URL 仅展示响应格式，不代表一个长期存在的真实对象。只有在 CDN 持久化未完成、且原始媒体地址经即时校验仍能下载到有效 WAV 文件时，`file_url` 才可能保留该地址；地址已失效或文件校验失败时，请求会返回失败或超时，不会把不可下载的地址作为成功结果。请在任务完成后及时下载并妥善保存，具体保留周期以平台当前存储策略为准。
