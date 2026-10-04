# Producer 下载WAV API 对接说明

Producer 允许我们下载歌曲相关的WAV文件，本文档讲解相关 API 的对接方法。

该 API 只有一个输入参数，就是 `audio_id`，它是歌曲唯一的ID。

这里我们输入的 `audio_id` 是 `a54609c6-13e2-4176-be0f-4d7eebc68e1f`，是一个Producer生成的歌曲ID。

```bash
curl -X POST 'https://api.acedata.cloud/producer/wav' \
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
  "task_id": "44963173-b6c5-463c-915f-96730d14ec63",
  "trace_id": "f75d6a27-54bc-49fd-a40e-6d4cd0427764",
  "data": [
    {
      "title": "Woke up with the sun in my eyes",
      "file_url": "https://cdn.acedata.cloud/assets/examples/fish/64adc04b-c196-4a0f-9070-222ba101ce6c-fc50de38c165.wav"
    }
  ]
}
```

可以看到，`data` 的 `file_url` 字段就是下载的WAV链接。
