# GPT Image 2 / 2.5 图像生成 API

## 1. 获取 API Key

打开 [Ace Data Cloud 应用列表](https://platform.acedata.cloud/console/applications)，进入可用的应用并复制 API Key。

![获取 Ace Data Cloud API Key](https://cdn.acedata.cloud/dvc3cg.jpg)

## 2. 发送第一个请求

```bash
curl https://api.acedata.cloud/openai/images/generations \
  -H "Authorization: Bearer 你的 API Key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-image-2",
    "prompt": "Minimal editorial product illustration: one plain white ceramic coffee mug centered on a solid cobalt blue tabletop, pale cream background, soft shadow, clean geometric shapes, no text, no logo, portrait composition",
    "size": "1024x1536"
  }'
```

成功响应的图片位于 `data[].url`。下面是 2026 年 9 月 8 日通过 Ace Data Cloud 实际请求得到的 1024×1536 结果（任务 `d56455e2-e7f7-4bcd-b935-475b0a1e0948`，trace `eb938601-8192-407f-b539-1e0554b697ec`）：

![GPT Image 2 生成的白色马克杯](https://cdn.acedata.cloud/18240dc44b9c.png)

## 3. 常用参数

| 字段 | 说明 |
| --- | --- |
| `model` | `gpt-image-2`（默认推荐）、`gpt-image-2.5-flare`（更快）或 `gpt-image-2.5-sunburst`（更高保真与控制）；三者均可选择对应的 `:official` 变体，`gpt-image-2` 还支持 `:reverse` |
| `prompt` | 图片描述，最长 32,000 个字符 |
| `size` | `auto` 或 `WIDTHxHEIGHT`；宽高须为 16 的倍数，长边不超过 3840，总像素为 655,360–8,294,400，宽高比不超过 3:1 |
| `n` | 1–10；`response_format=b64_json` 时仅支持 1 |
| `quality` | `low`、`medium`、`high` 或 `auto`；不同线路的支持和计费方式不同 |
| `response_format` | `url` 或 `b64_json` |
| `callback_url` | 可选；长任务完成后向该地址发送结果 |

常用尺寸：

| 比例 | 1K | 2K | 4K |
| --- | --- | --- | --- |
| 1:1 | `1024x1024` | `2048x2048` | `2880x2880` |
| 4:3 | `1536x1024` | `2048x1536` | `3264x2448` |
| 3:4 | `1024x1536` | `1536x2048` | `2448x3264` |
| 16:9 | `1792x1024` | `2048x1152` | `3840x2160` |
| 9:16 | `1024x1792` | `1152x2048` | `2160x3840` |

`size: "auto"` 会根据提示词中的比例、像素和版式意图选择画幅；需要精确像素时直接填写尺寸。

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

## 4. 多张生成

```bash
curl https://api.acedata.cloud/openai/images/generations \
  -H "Authorization: Bearer 你的 API Key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-image-2",
    "prompt": "A small fox reading under a glowing mushroom, watercolor illustration",
    "size": "1536x1024",
    "n": 2
  }'
```

`gpt-image-2`、`gpt-image-2.5-flare`、`gpt-image-2.5-sunburst` 与 `gpt-image-2:reverse` 按成功张数计费；`gpt-image-2:official`、`gpt-image-2.5-flare:official` 和 `gpt-image-2.5-sunburst:official` 根据响应中的文字输入和图片输出实际 Token 结算。页面价格是请求前估算，最终以使用记录为准。

## 5. 异步回调

请求体加入 `callback_url` 后，接口会先返回 `{"task_id": "..."}`，完成时向该 URL POST 最终结果；同步请求仍返回 `created` 和 `data`：

```json
{
  "model": "gpt-image-2",
  "prompt": "A product poster with clear typography",
  "size": "1024x1024",
  "callback_url": "https://example.com/webhooks/images"
}
```

回调接收方应使用 `task_id` 去重，并验证请求来源与数据格式。

## 6. 排错

| 状态 | 检查 |
| --- | --- |
| 400 | `model`、`prompt`、尺寸格式、`n` 与 `response_format` 组合 |
| 401 | API Key 是否完整，Header 是否为 `Authorization: Bearer ...` |
| 429 | 请求过于频繁，稍后重试 |
| 504 | 同步生成超时；改用 `callback_url` |

错误响应会包含 `error.code`、`error.message` 和 `trace_id`。反馈问题时提供 `trace_id`，不要提供 API Key。

完整字段和实时枚举以 [OpenAI Images Generations API](https://platform.acedata.cloud/documents/openai-images-generations) 页面为准。图像编辑请查看 [GPT Image 2 / 2.5 图像编辑](https://platform.acedata.cloud/documents/openai-images-edits)。
