# 电商口播集成指南

通过 `POST /kling/video-commerce` 提交任务，使用已有 `POST /kling/tasks` 查询平台任务状态。

## 输入

上传一张人物图并指定 voice_id，或使用一个预设 avatar_id（二者互斥，预设人物不能另指定 voice_id）。必须提供一个最多 2000 字的 speech_script。提供商品信息时，至少需要一张 ref_image 和一个 goods_title；商品口播不支持 speech_rate。普通人物口播支持 0.8、1.0 或 1.2 倍语速。

以下是请求结构示例，请替换素材 URL 后调用。

```json
{
  "contents": [
    {
      "type": "avatar_image",
      "url": "https://your-cdn.example/person.jpg"
    },
    {
      "type": "ref_image",
      "url": "https://your-cdn.example/product.jpg"
    },
    {
      "type": "goods_title",
      "text": "你的商品或口播内容"
    },
    {
      "type": "speech_script",
      "text": "你的商品或口播内容"
    }
  ],
  "settings": {
    "resolution": "720p",
    "voice_id": "male_calm_informative"
  },
  "async": true
}
```

## 结果与计费

同步模式返回生成结果；异步模式先返回 `task_id`，完成结果包含 `data` 中的视频或图片链接及服务端计算的 `usage`。`callback_url` 用于完成通知；`watermark=true` 请求同时返回水印版本。

普通人物口播：720p 为 1.4 Credits/秒、1080p 为 1.68 Credits/秒；商品口播：720p 为 1.96 Credits/秒、1080p 为 2.24 Credits/秒。 视频按实际生成时长结算，生成前的每秒基础价不代表整项任务总价。失败任务不收取生成费用。
