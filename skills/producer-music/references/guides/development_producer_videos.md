# Producer 下载视频 API 对接说明

Producer 允许我们下载歌曲相关的视频，本文档讲解相关 API 的对接方法。

该 API 只有一个输入参数，就是 `audio_id`，它是歌曲唯一的ID。

这里我们输入的 `audio_id` 是 `a54609c6-13e2-4176-be0f-4d7eebc68e1f`，是一个Producer生成的歌曲ID。

```bash
curl -X POST 'https://api.acedata.cloud/producer/videos' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "audio_id": "a54609c6-13e2-4176-be0f-4d7eebc68e1f"
}'
```

结果如下：

```
{
  "success": true,
  "task_id": "1237fc8f-ed3f-41fd-a889-a737fd7777da",
  "trace_id": "19db6190-d9ef-4a4f-a102-9f51b611c8b5",
  "data": {
    "video_url": "https://cdn.acedata.cloud/assets/examples/gemini/04a043bd-6b23-4b4e-945c-ce48158c3eee-3a89912507c7.mp4"
  }
}
```

可以看到，`data` 的 `video_url` 字段就是下载的视频链接。
