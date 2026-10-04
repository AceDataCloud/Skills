# Qwen Image 生成与编辑 API

`POST https://api.acedata.cloud/qwen-image/images` 通过同一接口完成文生图和 1–3 张参考图编辑，支持 `qwen-image-3.0` 与 `qwen-image-3.0-pro`。

## 选择模型

| 模型 | 适合场景 | 官方标准价 |
|---|---|---|
| `qwen-image-3.0` | 批量创作、快速迭代 | 输出 $0.030/张 |
| `qwen-image-3.0-pro` | 复杂排版、高精度成片 | 1K $0.040/张；2K $0.075/张 |

参考图按真实输入数量计费，官方标准价 $0.003/张。

## 同步生成

```bash
curl -X POST 'https://api.acedata.cloud/qwen-image/images' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen-image-3.0",
    "prompt": "A simple red circle centered on a clean white background.",
    "size": "1024*1024",
    "n": 1,
    "watermark": false
  }'
```

成功响应包含永久 CDN 图片地址、真实 usage 和本次费用：

```json
{
  "success": true,
  "task_id": "565a7f55-72c6-43ed-b274-268ff046e5b4",
  "trace_id": "bb923cec-1550-43b4-8df2-288ac0977b4b",
  "data": [
    {"image_url": "https://cdn.acedata.cloud/assets/examples/qwen-image/40d5c76b-2f84-4b04-9ea0-b706417ae622-bac6a9e9de22.png"}
  ],
  "usage": {
    "input_image_count": 0,
    "output_image_count": 1,
    "output_image_type": "qima_output_1k",
    "output_width": 1024,
    "output_height": 1024
  },
  "cost": {"amount": 0.322, "currency": "credit", "list_amount": 0.35}
}
```

## 参考图编辑

增加 `image_urls`，支持 1–3 张公开可访问图片：

```json
{
  "model": "qwen-image-3.0-pro",
  "prompt": "保留主体，将背景改成暖色电影海报风格",
  "image_urls": ["https://cdn.acedata.cloud/assets/examples/qwen-image/40d5c76b-2f84-4b04-9ea0-b706417ae622-bac6a9e9de22.png"],
  "size": "2048*2048",
  "n": 1,
  "watermark": false
}
```

`prompt_extend_mode=agent` 仅用于文生图。`n` 范围为 1–6；宽高比须在 1:8 至 8:1 之间。

## 异步任务

设置 `async: true` 后接口立即返回 `task_id`。使用 `/qwen-image/tasks` 查询终态，或传入 `callback_url` 接收完成通知。生成只结算一次，任务查询不重复计费。
