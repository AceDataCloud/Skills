# 商品视频集成指南

通过 `POST /kling/goods-studio` 提交任务，使用已有 `POST /kling/tasks` 查询平台任务状态。

## 输入

提供 1–5 张商品图和一个最多 200 字的商品标题；商品描述可选，最多 2000 字。时长可选 15、30 或 60 秒。

以下是请求结构示例，请替换素材 URL 后调用。

```json
{
  "contents": [
    {
      "type": "ref_image",
      "url": "https://your-cdn.example/product.jpg"
    },
    {
      "type": "goods_title",
      "text": "你的商品或口播内容"
    }
  ],
  "settings": {
    "resolution": "720p",
    "aspect_ratio": "16:9",
    "duration": 15
  },
  "async": true
}
```

## 结果与计费

同步模式返回生成结果；异步模式先返回 `task_id`，完成结果包含 `data` 中的视频或图片链接及服务端计算的 `usage`。`callback_url` 用于完成通知；`watermark=true` 请求同时返回水印版本。

720p：2.38 Credits/秒；1080p：2.8 Credits/秒。 视频按实际生成时长结算，生成前的每秒基础价不代表整项任务总价。失败任务不收取生成费用。
