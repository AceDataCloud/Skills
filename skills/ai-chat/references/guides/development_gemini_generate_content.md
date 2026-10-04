# Gemini Generate Content API 使用说明

Google Gemini 是一个非常强大的 AI 对话系统，通过输入提示就能在几秒内生成流畅自然的回复。本文档主要描述 Gemini Generate Content API 的使用方法，这是 Google 官方原生 API 格式，支持 `generateContent` 和 `streamGenerateContent` 两个端点。

## 与 Chat Completions API 的区别

Gemini Generate Content API 使用 Google 官方原生请求格式（`contents` 字段），而不是 OpenAI 兼容格式（`messages` 字段）。如果你已经使用 Google Gemini SDK 或熟悉官方 API 格式，可以直接使用此 API 而无需修改请求格式。

## 当前支持范围

当前支持文本、图片、视频、思考配置和自定义函数声明。以下能力暂不开放：

- 音频输入或音频输出；
- `codeExecution`、`googleSearch`、`urlContext` 等内置工具；
- `cachedContent` 显式上下文缓存。

这些能力需要完整、可核验的细分用量后才能准确计费；提交相关字段时接口会返回明确的 `400`，不会静默忽略或按普通文本计费。

## 申请流程

使用 Gemini Generate Content API 前，请先访问 [Gemini Generate Content API](https://platform.acedata.cloud/documents/gemini-generate-content-api) 页面，点击 "获取" 按钮来获得请求所需的凭证。

如果尚未登录或注册，会自动跳转到登录页面。首次申请会有免费额度。

## 基本用法

### Non-Streaming（非流式）

发送 POST 请求到 `/v1beta/models/{model}:generateContent`：

> **提示**：`gemini-3.x` 系列 flash 为思考模型，会先消耗 reasoning tokens；请把 `generationConfig.maxOutputTokens` 设到 512 以上，否则可能只返回空内容。

```bash
curl -X POST "https://api.acedata.cloud/v1beta/models/gemini-3.5-flash:generateContent" \
  -H "Authorization: Bearer your_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [
      {
        "role": "user",
        "parts": [
          {
            "text": "你好，请介绍一下你自己"
          }
        ]
      }
    ]
  }'
```

返回结果示例：

```json
{
  "candidates": [
    {
      "content": {
        "role": "model",
        "parts": [{"text": "你好！很高兴与你交流。"}]
      },
      "finishReason": "MAX_TOKENS"
    }
  ],
  "usageMetadata": {
    "promptTokenCount": 6,
    "candidatesTokenCount": 19,
    "thoughtsTokenCount": 489,
    "totalTokenCount": 514
  },
  "usage": {
    "prompt_tokens": 6,
    "completion_tokens": 19,
    "total_tokens": 514,
    "thoughts_tokens": 489,
    "cost": {
      "amount": 0.008860916380159999,
      "currency": "credit",
      "list_amount": 0.009631430847999998
    }
  },
  "modelVersion": "gemini-3.5-flash",
  "model": "gemini-3.5-flash"
}
```

`usageMetadata` 中的 token 字段会按原生 Gemini 语义计费：

- `promptTokenCount` 包含 `cachedContentTokenCount`，缓存命中的部分按缓存读取价格计算，不会重复计为普通输入。
- `promptTokensDetails` 与 `cacheTokensDetails` 会规范化为 `usage.prompt_tokens_details` 下的 `text_tokens`、`image_tokens`、`video_tokens`、`audio_tokens` 及对应 `cached_*` 明细。这些值分别包含在 `prompt_tokens` 与 `cached_tokens` 中；不同模态仅按各自价格重算，不会重复计费。
- `candidatesTokenCount` 和 `thoughtsTokenCount` 均按输出 token 价格计算。
- `toolUsePromptTokenCount` 是独立的工具输入 token，按输入 token 价格计算。

Ace Data Cloud 额外返回规范化的 `usage` 对象，跨模型协议统一从 `usage.cost` 读取本次调用费用。`cost` 是可选的费用预览；价格预览暂时不可用时，模型响应仍会正常返回，但可能不包含该字段。最终账单以用量记录为准。

### Streaming（流式）

发送 POST 请求到 `/v1beta/models/{model}:streamGenerateContent?alt=sse`：

```bash
curl -X POST "https://api.acedata.cloud/v1beta/models/gemini-2.5-flash:streamGenerateContent?alt=sse" \
  -H "Authorization: Bearer your_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [
      {
        "role": "user",
        "parts": [
          {
            "text": "写一首关于春天的诗"
          }
        ]
      }
    ]
  }'
```

流式返回会以 SSE（Server-Sent Events）格式逐步返回内容。中间事件通常只包含增量内容；含权威用量的终态事件会包含 `usageMetadata` 和规范化的 `usage`，费用仍位于 `usage.cost`：

```text
data: {"candidates":[{"content":{"parts":[{"text":"Hello!"}],"role":"model"},"index":0}],"modelVersion":"gemini-3.1-flash-lite","model":"gemini-3.1-flash-lite"}

data: {"candidates":[{"content":{"parts":[],"role":"model"},"finishReason":"STOP","index":0}],"usageMetadata":{"promptTokenCount":7,"candidatesTokenCount":89,"totalTokenCount":96},"usage":{"prompt_tokens":7,"completion_tokens":89,"total_tokens":96,"cost":{"amount":0.00026161075472,"currency":"credit","list_amount":0.000284359516}},"modelVersion":"gemini-3.1-flash-lite","model":"gemini-3.1-flash-lite"}

```

连接关闭即表示流结束；原生 Gemini 流不会发送 `data: [DONE]`。如果终态价格预览暂时不可用，`usage` 仍会返回 token 用量，但会省略 `cost`。

## 支持的模型

| 模型名称 | 说明 |
| --- | --- |
| `gemini-3.8-flash` | 最新 Flash 模型，适合高质量通用任务 |
| `gemini-3.7-flash` | 高质量通用 Flash 模型 |
| `gemini-3.6-flash` | 稳定的高性能多模态模型 |
| `gemini-3.5-flash` | 高吞吐多模态模型 |
| `gemini-3.5-flash-lite` | 低延迟、低成本模型 |
| `gemini-3.1-flash-lite` | 稳定版轻量模型 |
| `gemini-3.1-pro-preview` | 复杂推理与编码模型 |
| `gemini-3-flash-preview` | Gemini 3 Flash 预览模型 |
| `gemini-2.5-pro` | Gemini 2.5 Pro 模型 |
| `gemini-2.5-flash` | Gemini 2.5 Flash 模型 |
| `gemini-2.5-flash-lite` | Gemini 2.5 Flash-Lite 模型 |
| `gemini-3.1-flash-image` | 图像生成模型 |
| `gemini-3-pro-image` | 高质量图像生成模型 |
| `gemini-2.5-flash-image` | Gemini 2.5 图像生成模型 |

## 高级功能

### 系统指令

```json
{
  "contents": [
    {
      "role": "user",
      "parts": [{"text": "你好"}]
    }
  ],
  "systemInstruction": {
    "parts": [{"text": "你是一个专业的诗人，所有回复都用诗歌形式。"}]
  }
}
```

### 生成配置

```json
{
  "contents": [
    {
      "role": "user",
      "parts": [{"text": "讲一个故事"}]
    }
  ],
  "generationConfig": {
    "temperature": 0.7,
    "maxOutputTokens": 1024,
    "topP": 0.9,
    "topK": 40
  }
}
```

### JSON 模式

```json
{
  "contents": [
    {
      "role": "user",
      "parts": [{"text": "列出三个中国城市及其人口"}]
    }
  ],
  "generationConfig": {
    "responseMimeType": "application/json",
    "responseSchema": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "city": {"type": "string"},
          "population": {"type": "integer"}
        }
      }
    }
  }
}
```

### 思考模式（Thinking）

支持思考功能的模型（如 gemini-2.5-flash、gemini-2.5-pro）可以启用思考模式：

```json
{
  "contents": [
    {
      "role": "user",
      "parts": [{"text": "解释量子纠缠"}]
    }
  ],
  "generationConfig": {
    "thinkingConfig": {
      "includeThoughts": true,
      "thinkingBudget": 2048
    }
  }
}
```

### 函数调用

```json
{
  "contents": [
    {
      "role": "user",
      "parts": [{"text": "北京现在的天气怎么样？"}]
    }
  ],
  "tools": [
    {
      "functionDeclarations": [
        {
          "name": "get_weather",
          "description": "获取指定城市的天气信息",
          "parameters": {
            "type": "object",
            "properties": {
              "city": {
                "type": "string",
                "description": "城市名称"
              }
            },
            "required": ["city"]
          }
        }
      ]
    }
  ]
}
```

### 多轮对话

```json
{
  "contents": [
    {
      "role": "user",
      "parts": [{"text": "你好，我叫小明"}]
    },
    {
      "role": "model",
      "parts": [{"text": "你好小明！很高兴认识你。"}]
    },
    {
      "role": "user",
      "parts": [{"text": "我叫什么名字？"}]
    }
  ]
}
```

### 图片理解

```json
{
  "contents": [
    {
      "role": "user",
      "parts": [
        {"text": "描述这张图片"},
        {
          "inlineData": {
            "mimeType": "image/jpeg",
            "data": "base64_encoded_image_data..."
          }
        }
      ]
    }
  ]
}
```

## 安全设置

可通过 `safetySettings` 控制内容过滤：

```json
{
  "contents": [...],
  "safetySettings": [
    {
      "category": "HARM_CATEGORY_HARASSMENT",
      "threshold": "BLOCK_ONLY_HIGH"
    }
  ]
}
```

## 错误处理

| HTTP 状态码 | 含义 |
|------------|------|
| 400 | 请求参数无效 |
| 401 | 认证失败，请检查 Token |
| 403 | 内容被安全过滤器拦截 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |
