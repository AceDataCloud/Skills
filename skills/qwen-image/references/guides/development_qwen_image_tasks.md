# Qwen Image 任务查询 API

`POST https://api.acedata.cloud/qwen-image/tasks` 用于查询、批量查询或删除 Qwen Image 异步任务。该接口不产生额外 API 消耗。

## 查询单个任务

```bash
curl -X POST 'https://api.acedata.cloud/qwen-image/tasks' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"action":"retrieve","id":"TASK_ID"}'
```

任务完成后，`response.data` 包含永久 CDN 图片地址，`response.usage` 包含真实输入/输出数量，`response.cost` 为生成任务的结算信息。

## 批量查询

```json
{"action":"retrieve_batch","ids":["TASK_ID_1","TASK_ID_2"]}
```

返回 `{ "items": [...], "count": 2 }`。列表查询还支持按用户、应用和创建时间范围筛选。

## 删除任务记录

```json
{"action":"delete","id":"TASK_ID"}
```

删除只影响任务历史记录，不会删除已生成的 CDN 文件。
