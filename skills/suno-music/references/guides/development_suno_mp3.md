# Suno MP3 URL API 对接说明

Suno MP3 URL API 为已有音乐生成一个路径以 `.mp3` 结尾的可播放地址，适用于旧下载链接失效、移动端播放或需要重新获取公开音频 URL 的场景。

必填参数 `audio_id` 是 Suno 音频生成接口返回的音频 ID。每次调用都会创建独立的 MP3 URL 任务，不会修改原始音乐生成任务，也不会改变原音频 ID。

## 同步调用

```python
import requests

response = requests.post(
    "https://api.acedata.cloud/suno/mp3",
    headers={
        "accept": "application/json",
        "authorization": "Bearer <YOUR_API_TOKEN>",
        "content-type": "application/json"
    },
    json={"audio_id": "ef1ec21e-1540-4eb6-8fa5-26cb8b90d28f"},
    timeout=240
)
response.raise_for_status()
result = response.json()
print(result["data"][0]["file_url"])
```

成功时，`data[0].file_url` 是可播放音频地址。接口会优先转存到 `https://cdn.acedata.cloud/suno/{audio_id}.mp3`；如果持久化失败，则返回当前可用的原始媒体地址。

## 异步调用

处理时间较长时，可传入 `async: true`：

```python
submission = requests.post(
    "https://api.acedata.cloud/suno/mp3",
    headers={"authorization": "Bearer <YOUR_API_TOKEN>"},
    json={
        "audio_id": "ef1ec21e-1540-4eb6-8fa5-26cb8b90d28f",
        "async": True
    }
).json()

export_task_id = submission["task_id"]
```

随后通过 `/suno/tasks` 查询 `export_task_id`。也可以提供 `callback_url`，在任务完成后接收最终结果。同步响应、任务查询和回调使用相同的终态数据结构。

## 注意事项

- `audio_id` 必须来自可识别的 Suno 音频。
- MP3 URL 任务与原音乐生成任务相互独立。
- 持久化失败不会阻塞结果，会回退到原始媒体地址；请及时下载。
- 建议业务侧在拿到结果后及时下载并按自己的数据保留策略保存。
