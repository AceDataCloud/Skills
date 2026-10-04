# GPT Image 2 / 2.5 图像编辑 API

## 1. 获取 API Key

打开 [Ace Data Cloud 应用列表](https://platform.acedata.cloud/console/applications)，进入可用的应用并复制 API Key。

![获取 Ace Data Cloud API Key](https://cdn.acedata.cloud/dvc3cg.jpg)

## 2. 使用图片 URL 编辑

原图：

![GPT Image 2 编辑原图](https://cdn.acedata.cloud/18240dc44b9c.png)

```bash
curl https://api.acedata.cloud/openai/images/edits \
  -H "Authorization: Bearer 你的 API Key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-image-2",
    "image": "https://cdn.acedata.cloud/assets/examples/gpt-image/d56455e2-e7f7-4bcd-b935-475b0a1e0948_0-18240dc44b9c.png",
    "prompt": "Keep the mug, tabletop, camera angle, portrait layout, and soft shadow unchanged. Change only the mug color from white to vivid orange and the pale cream background to solid dark navy blue. No text and no logo.",
    "size": "1024x1536"
  }'
```

成功响应：

```json
{
  "success": true,
  "task_id": "49848451-c624-4df9-9dc2-494018daaf4c",
  "trace_id": "5ac021c2-2891-4eed-bfcf-4c6668ac1be1",
  "created": 1788831893,
  "model": "gpt-image-2",
  "data": [
    {
      "url": "https://cdn.acedata.cloud/assets/examples/gpt-image/49848451-c624-4df9-9dc2-494018daaf4c_0-b6d780a732ca.png"
    }
  ],
  "usage": {
    "input_tokens": 775,
    "output_tokens": 1372,
    "total_tokens": 2147
  }
}
```

这是 2026 年 9 月 8 日通过 Ace Data Cloud 实际完成的编辑结果，杯子变为橙色、背景变为深海军蓝，并保持原始构图和 1024×1536 尺寸：

![GPT Image 2 橙色马克杯编辑结果](https://cdn.acedata.cloud/b6d780a732ca.png)

## 3. 上传本地图片

使用 `multipart/form-data`：

```bash
curl https://api.acedata.cloud/openai/images/edits \
  -H "Authorization: Bearer 你的 API Key" \
  -F "model=gpt-image-2" \
  -F "image=@input.png" \
  -F "prompt=Replace the background with a bright modern studio"
```

可重复传入 `image`，GPT Image 系列最多支持 16 张参考图。JSON 请求中的 `image` 可以是单个 URL 或 URL 数组；本地文件使用 multipart 上传。

### 模型与计费方式

| 模型 | 适用场景与计费方式 |
| --- | --- |
| `gpt-image-2` | 默认逆向通道，按成功图片张数固定计费 |
| `gpt-image-2:reverse` | 显式选择逆向通道，按成功图片张数固定计费 |
| `gpt-image-2:official` | 官方 API 通道，稳定性更高，按实际 Token 用量计费 |
| `gpt-image-2.5-flare` | 侧重生成速度，按成功图片张数固定计费 |
| `gpt-image-2.5-flare:official` | 官方 API 通道，稳定性更高且侧重生成速度，按实际 Token 用量计费 |
| `gpt-image-2.5-sunburst` | 侧重高保真与精细控制，按成功图片张数固定计费 |
| `gpt-image-2.5-sunburst:official` | 官方 API 通道，稳定性更高且侧重高保真与精细控制，按实际 Token 用量计费 |

官方 API 通道的页面价格是请求前估算，最终以响应中的实际 Token 用量和使用记录为准。

## 4. 使用蒙版局部编辑

官方 Images Edit 接口通过 `mask` 指定允许修改的区域。Ace Data Cloud 的 `:official` 模型遵循相同的 multipart 契约：

- `mask` 必须是带 Alpha 通道的 PNG，大小不超过 4MB；
- 蒙版尺寸必须与第一张 `image` 完全一致；
- Alpha 为 `0` 的透明像素表示允许编辑，非透明像素表示应保留；
- 只有颜色为黑白、但没有透明通道的 RGB 图片不能作为有效蒙版；
- 提示词应描述期望得到的完整画面，同时明确局部修改和需要保持不变的内容。

下面先从原图生成一个蒙版。示例将中央矩形设为透明，只允许模型修改该区域：

```python
from PIL import Image, ImageDraw

source = Image.open("input.png").convert("RGBA")
mask = Image.new("RGBA", source.size, (0, 0, 0, 255))
draw = ImageDraw.Draw(mask)
width, height = source.size
draw.rectangle(
    (width // 4, height // 4, width * 3 // 4, height * 3 // 4),
    fill=(0, 0, 0, 0),
)
mask.save("mask.png")
```

然后把原图和蒙版一起上传：

```bash
curl https://api.acedata.cloud/openai/images/edits \
  -H "Authorization: Bearer 你的 API Key" \
  -F "model=gpt-image-2:official" \
  -F "image=@input.png" \
  -F "mask=@mask.png" \
  -F "prompt=Keep the composition, lighting, and all objects outside the transparent mask unchanged. Inside the masked area, replace the empty tabletop with a small blue ceramic vase."
```

也可以沿用 OpenAI 官方 Python SDK 的 `images.edit` 调用方式，只需把 `base_url` 指向 Ace Data Cloud：

```python
from openai import OpenAI

client = OpenAI(
    api_key="你的 API Key",
    base_url="https://api.acedata.cloud/openai",
)

with open("input.png", "rb") as image, open("mask.png", "rb") as mask:
    result = client.images.edit(
        model="gpt-image-2:official",
        image=image,
        mask=mask,
        prompt=(
            "Keep the composition, lighting, and all objects outside the "
            "transparent mask unchanged. Inside the masked area, replace "
            "the empty tabletop with a small blue ceramic vase."
        ),
    )

print(result.data[0].url)
```

使用 `mask` 时，原图和蒙版必须在同一个 multipart 请求中分别通过 `image=@input.png` 与 `mask=@mask.png` 上传。不要把 URL 原图与本地蒙版文件混合传入；纯 URL 编辑请求不支持再附加本地 `mask` 文件。蒙版会约束编辑区域，但生成模型仍可能对边缘进行自然融合；需要严格边界时，应使用清晰的 Alpha 边缘并在提示词中重复说明哪些内容必须保持不变。

以上调用方式与 [OpenAI Image Edit API](https://developers.openai.com/api/reference/python/resources/images/methods/edit) 和 [GPT Image 官方 Cookbook](https://developers.openai.com/cookbook/examples/generate_images_with_gpt_image) 的蒙版示例一致。

## 5. 常用参数

| 字段 | 说明 |
| --- | --- |
| `model` | `gpt-image-2`、`gpt-image-2.5-flare`（更快）或 `gpt-image-2.5-sunburst`（更高保真与控制）；三者均可选择对应的 `:official` 变体，`gpt-image-2` 还支持 `:reverse` |
| `image` | JSON 使用单个 URL 或最多 16 个 URL 的数组；multipart 使用一个或多个 `image` 文件字段。使用 `mask` 时必须上传本地图片文件 |
| `mask` | 可选 PNG 蒙版，仅限 multipart 文件上传；须带 Alpha 通道、与第一张 `image` 同尺寸且不超过 4MB |
| `prompt` | 编辑指令 |
| `size` | `auto` 或符合限制的 `WIDTHxHEIGHT` |
| `n` | 1–10；`response_format=b64_json` 时仅支持 1 |
| `response_format` | `url` 或 `b64_json` |
| `callback_url` | 可选异步回调地址 |

尺寸规则与生成接口一致：宽高须为 16 的倍数，长边不超过 3840，总像素为 655,360–8,294,400，宽高比不超过 3:1。省略 `size` 或使用 `auto` 时，模型会结合提示词和第一张参考图选择画幅。

`gpt-image-2`、`gpt-image-2.5-flare`、`gpt-image-2.5-sunburst` 与 `gpt-image-2:reverse` 按成功张数计费；`gpt-image-2:official`、`gpt-image-2.5-flare:official` 和 `gpt-image-2.5-sunburst:official` 根据文字输入、参考图输入和图片输出的实际 Token 结算，最终以使用记录为准。

## 6. 异步回调与排错

长任务可在请求中加入：

```json
{
  "callback_url": "https://example.com/webhooks/images"
}
```

异步 200 响应为 `{"task_id": "..."}`；完成后回调最终结果。同步请求则返回 `created` 和 `data`。

| 状态 | 检查 |
| --- | --- |
| 400 | 图片格式/数量、参数组合和尺寸格式；使用 `mask` 时检查 PNG Alpha 通道、4MB 限制及其尺寸是否与第一张原图一致 |
| 401 | API Key 与 Bearer Header |
| 429 | 请求频率 |
| 504 | 改用异步回调 |

错误响应会包含 `trace_id`。反馈问题时提供该 ID，不要提供 API Key。

完整字段和实时枚举以 [OpenAI Images Edits API](https://platform.acedata.cloud/documents/openai-images-edits) 页面为准。纯文本生成图片请查看 [GPT Image 2 / 2.5 图像生成](https://platform.acedata.cloud/documents/openai-images-generations)。
