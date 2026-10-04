# MiniMax H3 视频生成 API 对接指南

本文介绍 MiniMax H3 视频生成 API 的对接与使用。该接口支持文生视频、首尾帧控制与多模态参考生视频，使用统一的 V2 多模态 `content` 结构创建任务。

## 申请流程

要使用 MiniMax H3 视频生成 API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[MiniMax H3 视频生成 API →](https://platform.acedata.cloud/documents/minimax-videos-integration)

建议把 Token 保存为环境变量，不要写入源码或提交到版本库：

```bash
export ACEDATACLOUD_API_KEY="YOUR_API_KEY"
```

## 接口概览

- **Base URL**：`https://api.acedata.cloud`
- **Endpoint**：`POST /minimax/videos`
- **认证方式**：HTTP Header 中携带 `authorization: Bearer {token}`
- **请求头**：

  - `accept: application/json`
  - `content-type: application/json`

- **模型（model）**：`MiniMax-H3`
- **输入结构**：通过 `content` 统一传入文本、图片、视频和音频
- **输出模式**：默认同步等待生成完成并返回完整 `task`；传 `async: true` 或 `callback_url` 时立即返回 `task_id` 与 `trace_id`
- **结果查询**：通过 [MiniMax H3 任务查询 API](/documents/minimax-tasks-integration) 获取状态和成片
- **异步回调**：可选，通过 `callback_url` 接收最终任务结果

你不需要传 `action` 来选择生成模式，接口会根据 `content` 中的素材类型和 `role` 自动判断用途。

## 适合哪些场景

| 场景 | 输入组合 | 常见用途 |
| --- | --- | --- |
| 文生视频 | 文本 | 广告创意、分镜预演、短视频、氛围镜头 |
| 首帧图生视频 | 文本 + 首帧图片 | 让商品图、海报、人物照片或插画自然动起来 |
| 尾帧 / 首尾帧视频 | 文本 + 尾帧，或文本 + 首帧 + 尾帧 | 控制片头与片尾、转场、成长变化和前后对比 |
| 多模态参考生视频 | 文本 + 参考图片 / 视频 / 音频 | 保持角色和产品一致，复刻动作、运镜、音色或剪辑节奏 |

## 调用流程

默认不传 `async` 时，`/minimax/videos` 会等待生成完成并直接返回完整 `task`。需要立即释放连接时，传 `async: true` 或 `callback_url`：

1. 保存立即响应中的 `task_id` 和 `trace_id`。
2. 未配置回调时，每隔约 10 秒调用 `/minimax/tasks` 查询一次。
3. 当 `task.status` 变为 `succeeded` 时，从 `task.content.url` 获取视频。
4. 当状态为 `failed` 或 `cancelled` 时停止轮询，并读取 `task.error`。

## 顶层请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `model` | string | 是 | - | 固定为 `MiniMax-H3` |
| `content` | object[] | 是 | - | 多模态内容数组，必须包含一个非空 `text` 项 |
| `resolution` | string | 是 | - | `768P` 或 `2K` |
| `duration` | integer | 是 | - | 生成时长，4-15 秒整数 |
| `ratio` | string | 条件必填 | `adaptive` | `adaptive`、`21:9`、`16:9`、`4:3`、`1:1`、`3:4`、`9:16` |
| `async` | boolean | 否 | `false` | `true` 时立即返回任务标识，通过任务接口获取结果 |
| `callback_url` | string | 否 | - | 接收最终任务结果的公网回调 URL；提供后自动启用异步模式 |

`ratio` 的规则取决于工作流：

- **文生视频**：必填，且不能为 `adaptive`。
- **首帧、尾帧或首尾帧视频**：画幅由输入图片决定，建议省略或传 `adaptive`。
- **多模态参考生视频**：可省略，默认 `adaptive`；也可以明确指定一个固定比例。

接口不接受旧版或兼容字段，例如 `prompt`、`image_urls`、`audio_urls`、`messages` 和 `first_frame_image`。收到这类参数错误时，请删除旧字段并迁移到 `content`；例如把 `"prompt": "一只猫挥手"` 改为 `"content": [{"type": "text", "text": "一只猫挥手"}]`。不要同时发送新旧两种格式。

## content 内容项参数

每个内容项都必须有 `type`，其余字段由类型决定：

| `type` | 数据字段 | `role` | 说明 |
| --- | --- | --- | --- |
| `text` | `text` | 不传 | 每个请求必须包含一个非空文本项，最长 7000 字符 |
| `image_url` | `image_url.url` | `first_frame` | 首帧图片；只有一张图片且省略 `role` 时，也按首帧处理 |
| `image_url` | `image_url.url` | `last_frame` | 尾帧图片；可单独使用，也可与 `first_frame` 组合控制起点和终点 |
| `image_url` | `image_url.url` | `reference_image` | 参考主体、角色、产品、服装、场景或风格 |
| `video_url` | `video_url.url` | `reference_video` | 参考动作、运镜、表演或剪辑结构 |
| `audio_url` | `audio_url.url` | `reference_audio` | 参考音色、对白、音乐或节奏 |

媒体地址支持三种形式：

- 可公网访问的 HTTPS URL，推荐用于大文件。
- `mm_file://{file_id}`，引用已经上传或已有结果的文件。
- 对应媒体类型的 Base64 data URI。Base64 会使体积增加约三分之一，请确保整个请求体不超过 64 MB。

## 素材规格与数量限制

| 素材 | 格式 | 单文件限制 | 尺寸 / 时长 | 数量限制 |
| --- | --- | --- | --- | --- |
| 图片 | JPG、JPEG、PNG、WEBP、HEIC、HEIF | 不超过 30 MB | 宽高均为 256-5760 px；宽高比 0.4-2.5 | 首帧最多 1 张、尾帧最多 1 张、参考图最多 9 张 |
| 视频 | MP4、MOV；H.264/AVC 或 H.265/HEVC；音轨 AAC 或 MP3 | 不超过 50 MB | 每段 2-15 秒，合计不超过 15 秒；宽高均为 256-5760 px；宽高比 0.4-2.5；23.976-60 fps | 最多 3 段参考视频 |
| 音频 | WAV、MP3 | 不超过 15 MB | 每段 2-15 秒，合计不超过 15 秒 | 最多 3 段参考音频 |

多模态参考场景中的图片、视频和音频合计最多 12 个文件。首尾帧场景和参考素材场景互斥：一旦使用 `reference_image`、`reference_video` 或 `reference_audio`，就不能再使用 `first_frame` 或 `last_frame`，反之亦然。

## 生产级能力展示

下面不是概念图或占位素材，而是 MiniMax H3 官方生产级能力样片的真实参考输入与实际视频输出。三组案例分别覆盖品牌短片、真人叙事和时尚电商，适合评估模型在商业制作中最关键的能力。

| 能力 | 重点观察 |
| --- | --- |
| 人物与人脸一致性 | 多镜头切换后五官、发型、妆容和人物气质是否稳定 |
| 面部表演 | 近景中的眼神、微表情、情绪张力和自然头部运动 |
| 商品结构保持 | 眼镜、手袋等产品的轮廓、材质、佩戴关系和镜面反射 |
| 品牌视觉执行 | 场景氛围、电影颗粒、色彩、Logo 与剪辑节奏是否统一 |
| 电影化叙事 | 景别变化、人物调度、运镜、节奏和声音能否形成完整段落 |

这里的“人脸能力”指视频生成中的人物外观一致性、面部细节和表演控制，不是身份识别、人脸比对或换脸接口。

### 高端品牌短片：人物、产品与品牌资产统一

**制作目标：** 16:9 高级时装品牌片。以荒漠公路和复古汽车建立冷峻氛围，保持女主角外观与黑色手袋结构，并将品牌 Logo 自然纳入结尾。这个案例重点检验跨镜头人物一致性、商品保持、电影质感和品牌收束能力。

| 氛围与场景参考 | 人物参考 |
| --- | --- |
| <img src="https://cdn.acedata.cloud/uploads/6e65f865-f1c2-4f80-8b51-9a98d4d930b1" alt="荒漠公路与复古汽车的品牌片氛围参考" width="420"> | <img src="https://cdn.acedata.cloud/uploads/88d89cc3-e6cb-42b4-ab4c-1bbbf6c9f7c8" alt="品牌片女主角参考" width="420"> |

| 手袋产品参考 | 品牌 Logo 参考 |
| --- | --- |
| <img src="https://cdn.acedata.cloud/uploads/e91f7fff-f8e3-4da5-b882-87edbc3c9473" alt="黑色手袋产品参考" width="420"> | <img src="https://cdn.acedata.cloud/uploads/b68dac43-fb14-42b5-bf8b-fd4d65506520" alt="品牌 Logo 参考" width="420"> |

<video controls playsinline preload="metadata" poster="https://cdn.acedata.cloud/uploads/6e65f865-f1c2-4f80-8b51-9a98d4d930b1" style="display: block; width: 100%; max-width: 1080px; height: auto; margin: 16px auto; border-radius: 8px;" src="https://cdn.acedata.cloud/uploads/6845b11d-1a58-4478-afd8-29e7e117772a"></video>

[直接打开或下载品牌短片](https://cdn.acedata.cloud/uploads/6845b11d-1a58-4478-afd8-29e7e117772a)

对应的 `content` 组织方式：

```json
{
  "model": "MiniMax-H3",
  "content": [
    {
      "type": "text",
      "text": "15 秒、16:9 高级时装品牌片。荒漠公路旁停着复古汽车，女主从后备箱取出黑色手袋，与男主短暂对视后独自离开。保持人物、手袋与品牌视觉一致；冷峻高级，电影颗粒，剪辑利落，结尾自然呈现品牌 Logo。"
    },
    {
      "type": "image_url",
      "image_url": { "url": "https://cdn.acedata.cloud/uploads/6e65f865-f1c2-4f80-8b51-9a98d4d930b1" },
      "role": "reference_image"
    },
    {
      "type": "image_url",
      "image_url": { "url": "https://cdn.acedata.cloud/uploads/88d89cc3-e6cb-42b4-ab4c-1bbbf6c9f7c8" },
      "role": "reference_image"
    },
    {
      "type": "image_url",
      "image_url": { "url": "https://cdn.acedata.cloud/uploads/e91f7fff-f8e3-4da5-b882-87edbc3c9473" },
      "role": "reference_image"
    },
    {
      "type": "image_url",
      "image_url": { "url": "https://cdn.acedata.cloud/uploads/b68dac43-fb14-42b5-bf8b-fd4d65506520" },
      "role": "reference_image"
    }
  ],
  "resolution": "2K",
  "duration": 15,
  "ratio": "16:9"
}
```

### 真人竖屏短剧：人脸一致性与情绪表演

**制作目标：** 15 秒、9:16 暗黑浪漫短剧预告。通过男女主角参考图锁定人物外观，以古堡参考图约束空间；使用中近景与面部特写表现眼神对峙、恐惧、克制和危险感。这个案例适合观察真人五官稳定性、微表情、视线关系和连续表演。

| 男女主角参考 | 古堡场景参考 |
| --- | --- |
| <img src="https://cdn.acedata.cloud/uploads/f772a484-9ca5-46dd-b4a4-bb3b62d20086" alt="真人短剧男女主角参考" width="420"> | <img src="https://cdn.acedata.cloud/uploads/2305899b-8f5d-46e5-bba0-abd8d185691c" alt="暗黑古堡场景参考" width="420"> |

<video controls playsinline preload="metadata" poster="https://cdn.acedata.cloud/uploads/f772a484-9ca5-46dd-b4a4-bb3b62d20086" style="display: block; width: 100%; max-width: 520px; height: auto; margin: 16px auto; border-radius: 8px;" src="https://cdn.acedata.cloud/uploads/0f3e9bf2-5073-46f4-9a2d-7d8d912391cf"></video>

[直接打开或下载真人短剧](https://cdn.acedata.cloud/uploads/0f3e9bf2-5073-46f4-9a2d-7d8d912391cf)

提示词应明确人物关系、情绪和景别，而不只是描述“男女对话”：

```text
15 秒、9:16 真人暗黑浪漫短剧预告。女主误入禁忌古堡，唤醒沉睡的吸血鬼贵族；
他危险而克制地靠近，她恐惧但不屈服。保持两位角色的五官、发型与服装一致，
以中近景和面部特写表现眼神对峙与情绪张力，暗色电影光线，节奏紧凑。
```

### 时尚眼镜广告：人脸细节与商品结构保持

**制作目标：** 9:16 高级时尚眼镜广告。人物全身图负责身形与台步，人脸参考图负责五官和妆容，产品图负责环绕曲线、镜片反射、镜腿和猫眼轮廓。这个案例同时考验脸部近景、多人一致性、佩戴关系和商品几何结构。

| 模特与造型参考 | 人脸细节参考 | 眼镜产品参考 |
| --- | --- | --- |
| <img src="https://cdn.acedata.cloud/uploads/d1e00670-b618-4989-8daf-e2f57ee863ff" alt="时尚广告模特与造型参考" width="280"> | <img src="https://cdn.acedata.cloud/uploads/6371092e-58be-4a74-9492-b9de1847af8a" alt="模特人脸细节参考" width="280"> | <img src="https://cdn.acedata.cloud/uploads/4de062a9-ceb4-4619-bde1-6d90e4b19dad" alt="眼镜产品结构参考" width="280"> |

<video controls playsinline preload="metadata" poster="https://cdn.acedata.cloud/uploads/d1e00670-b618-4989-8daf-e2f57ee863ff" style="display: block; width: 100%; max-width: 520px; height: auto; margin: 16px auto; border-radius: 8px;" src="https://cdn.acedata.cloud/uploads/55715089-b6bd-4ef6-a3c2-e762a672f751"></video>

[直接打开或下载时尚眼镜广告](https://cdn.acedata.cloud/uploads/55715089-b6bd-4ef6-a3c2-e762a672f751)

在商品广告中，提示词应把人物参考和产品参考的职责分开写清楚：人物素材约束脸、妆容、身形和气质；产品素材约束轮廓、材质、反射和佩戴位置。这样比笼统地写“生成一条眼镜广告”更稳定。

## 文生视频

只有一个文本项时即为文生视频。适合从创意、脚本或镜头描述直接生成画面。提示词可以按“主体 + 动作 + 场景 + 镜头 + 光线 + 声音”的顺序组织。

```bash
curl -X POST 'https://api.acedata.cloud/minimax/videos' \
  -H "Authorization: Bearer $ACEDATACLOUD_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "MiniMax-H3",
    "content": [
      {
        "type": "text",
        "text": "15 秒电影级香水广告：清晨海岸的黑色礁石上，透明香水瓶被薄雾与海浪环绕。微距展现瓶身水珠和玻璃折射，镜头从产品特写缓慢拉升到广阔海面；银蓝色调，真实自然光，高级克制，结尾定格产品。"
      }
    ],
    "resolution": "2K",
    "duration": 15,
    "ratio": "16:9"
  }'
```

默认同步模式会在生成完成后返回完整任务：

```json
{
  "task": {
    "id": "f5977217-ed2c-40da-adbe-93d08235618f",
    "model": "MiniMax-H3",
    "status": "succeeded",
    "content": { "url": "https://cdn.acedata.cloud/minimax/f5977217.mp4" },
    "resolution": "2K",
    "duration": 15,
    "ratio": "16:9"
  }
}
```

若请求中加入 `"async": true`，接口立即返回：

```json
{
  "task_id": "f5977217-ed2c-40da-adbe-93d08235618f",
  "trace_id": "trace_7f8c2b1a"
}
```

## 首帧图生视频

将图片标记为 `first_frame`，模型会从该画面开始生成。适合让海报、商品图、角色设定图和摄影作品自然动起来。

```json
{
  "model": "MiniMax-H3",
  "content": [
    {
      "type": "text",
      "text": "人物自然呼吸并看向窗外，衣角被微风吹动，镜头缓慢推进"
    },
    {
      "type": "image_url",
      "image_url": {
        "url": "https://cdn.acedata.cloud/b1c82e4937.png"
      },
      "role": "first_frame"
    }
  ],
  "resolution": "2K",
  "duration": 5,
  "ratio": "adaptive"
}
```

## 尾帧和首尾帧视频

只提供 `last_frame` 可以让模型自然生成到指定画面；同时提供 `first_frame` 与 `last_frame`，可以明确控制起点和终点。适合转场、形态变化、成长过程或产品前后对比。

```json
{
  "model": "MiniMax-H3",
  "content": [
    {
      "type": "text",
      "text": "女孩从童年自然成长为青年，时间流逝平滑，人物始终位于画面中央"
    },
    {
      "type": "image_url",
      "image_url": { "url": "YOUR_FIRST_FRAME_URL" },
      "role": "first_frame"
    },
    {
      "type": "image_url",
      "image_url": { "url": "YOUR_LAST_FRAME_URL" },
      "role": "last_frame"
    }
  ],
  "resolution": "2K",
  "duration": 5,
  "ratio": "adaptive"
}
```

首帧与尾帧的尺寸和宽高比应尽量一致，主体位置、构图和光线差异不要过大，这样更容易得到自然过渡。

## 多模态参考生视频

参考素材可以组合使用：参考图片控制角色或产品外观，参考视频控制动作和运镜，参考音频控制对白音色、音乐或剪辑节奏。提示词中应明确说明每类素材要控制什么，避免只上传素材却不给出关联关系。

```json
{
  "model": "MiniMax-H3",
  "content": [
    {
      "type": "text",
      "text": "保持参考人物的五官、发型与服装一致，按照参考视频中的表演动作完成时尚短片；镜头节奏跟随参考音频，近景突出自然面部表情"
    },
    {
      "type": "image_url",
      "image_url": { "url": "YOUR_CHARACTER_IMAGE_URL" },
      "role": "reference_image"
    },
    {
      "type": "video_url",
      "video_url": { "url": "YOUR_PERFORMANCE_VIDEO_URL" },
      "role": "reference_video"
    },
    {
      "type": "audio_url",
      "audio_url": { "url": "YOUR_AUDIO_URL" },
      "role": "reference_audio"
    }
  ],
  "resolution": "2K",
  "duration": 5,
  "ratio": "adaptive"
}
```

## 回调通知

传入 `callback_url` 会自动启用异步模式：创建接口立即返回 `task_id` 和 `trace_id`，并在任务完成后向该地址 POST 最终结果，结构与任务查询响应一致。

回调中的最终状态为 `succeeded`、`failed` 或 `cancelled`。即使使用回调，也建议保存 `task_id`，以便主动查询或补偿漏掉的通知。

## 常见错误

| HTTP 状态码 | 含义 | 处理建议 |
| --- | --- | --- |
| `400` | 参数错误或素材组合不合法 | 检查必填字段、`role`、素材数量和格式 |
| `401` | Token 缺失或无效 | 检查 `Authorization: Bearer ...` |
| `402` | 余额或额度不足 | 在控制台补充通用余额 |
| `422` | 内容安全检查未通过 | 调整提示词或素材后重新提交 |
| `429` | 请求过于频繁 | 指数退避后重试；任务轮询建议间隔约 10 秒 |
| `500` | 服务暂时不可用 | 保留请求信息，稍后重试 |

同步响应中的 `task.status: succeeded` 表示视频已生成；异步确认只代表任务已进入队列。只有任务最终成功时才会计费，查询任务本身免费，不会重复扣费。

### H3 Max

`MiniMax-H3-Max` 支持 480P 或 768P、5–15 秒整数时长。音频输入不额外计费，前 2 张图片免费，超出部分逐张计费；参考视频按实际输入时长计费。该模型不支持 2K。
