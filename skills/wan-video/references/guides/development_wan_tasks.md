# Wan 任务查询 API

`POST https://api.acedata.cloud/wan/tasks` 用于查询、批量查询或删除 Wan 视频任务。任务查询不重复收取生成费用。

## 查询单个任务

```bash
curl -X POST 'https://api.acedata.cloud/wan/tasks' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"action":"retrieve","id":"TASK_ID"}'
```

完成任务的 `response.data.video_url` 为永久 CDN 地址；`response.usage` 包含分辨率、输入/输出视频秒数、帧率和比例；`response.cost` 为生成任务结算。

## 批量查询

```json
{"action":"retrieve_batch","ids":["TASK_ID_1","TASK_ID_2"]}
```

返回 `{ "items": [...], "count": 2 }`。任务进行中时可能尚无 `finished_at` 和最终 `response`。

## 删除任务记录

```json
{"action":"delete","id":"TASK_ID"}
```

删除只影响任务历史记录，不会删除已生成的 CDN 视频。
