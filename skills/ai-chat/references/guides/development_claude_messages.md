# Claude Messages API 申请及使用

Anthropic Claude 是一款非常强大的 AI 对话系统，只要输入提示词，就能在短短几秒内生成流畅自然的回复。Claude Messages API 是 Anthropic 官方原生的 API 格式，与 OpenAI 兼容格式（Chat Completion）不同，它采用 Anthropic 自有的请求和响应结构，能够更好地利用 Claude 的独特能力，如多模态内容输入、工具调用、深度思考（Extended Thinking）等高级特性。

本文档主要介绍 Claude Messages API 操作的使用流程，利用它我们可以使用与 Anthropic 官方一致的原生接口来调用 Claude 的对话功能。

## 申请流程

要使用 Claude Messages API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Claude Messages API →](https://platform.acedata.cloud/documents/claude-messages)

## 基本使用

Claude Messages API 的请求路径为 `/v1/messages`，与 Anthropic 官方 API 保持一致。我们至少需要提供三个必填参数：

- `model`：选择使用的 Claude 模型。`claude-opus-5-5` 仅通过 Messages API 提供，支持 100 万 Token 上下文、最大输出 128K Token，并始终启用自适应思考。最新旗舰为 `claude-fable-5-1`（100 万 Token 上下文、最大输出 128K Token）；原 `claude-fable-5` 仍兼容保留。 `claude-sonnet-5-5` 已加入原生 Messages 系列接口，支持图像输入和自适应思考；其输入、输出和缓存读取官方参考价分别为每百万 Token 2、10 和 0.20 美元。
- `messages`：输入的消息数组，每条消息包含 `role`（角色）和 `content`（内容），其中 `role` 支持 `user` 和 `assistant`。
- `max_tokens`：最大输出 token 数，用于限制单次回复的长度。

常用可选参数：

- `system`：系统提示词，用于设定模型的行为和角色。
- `temperature`：生成随机性，0-1 之间，值越大回复越发散。
- `stream`：是否使用流式响应，设为 `true` 可实现逐字返回效果。
- `stop_sequences`：自定义停止序列，模型遇到这些文本时会停止生成。
- `top_p`：核采样参数，与 temperature 配合控制生成的随机性。
- `top_k`：仅从概率最高的 K 个选项中采样。
- `tools`：工具定义，用于让模型调用外部函数。
- `tool_choice`：控制模型如何使用提供的工具。
- `cache_control`：在请求的最后一个可缓存内容块处自动创建缓存断点；也可写在具体内容块上。

### cURL 示例

```bash
curl -X POST 'https://api.acedata.cloud/v1/messages' \
  -H 'accept: application/json' \
  -H 'authorization: Bearer {token}' \
  -H 'content-type: application/json' \
  -d '{
    "model": "claude-fable-5-1",
    "max_tokens": 1024,
    "messages": [
      {
        "role": "user",
        "content": "Hello, Claude"
      }
    ]
  }'
```

### Python 示例

```python
import requests

url = "https://api.acedata.cloud/v1/messages"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "model": "claude-fable-5-1",
    "max_tokens": 1024,
    "messages": [
        {"role": "user", "content": "Hello, Claude"}
    ]
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

调用之后，返回结果如下：

```json
{
  "id": "msg_013Zva2CMHLNnXjNJJKqJ2EF",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Hi! My name is Claude. How can I help you today?"
    }
  ],
  "model": "claude-opus-4-8",
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 12,
    "output_tokens": 15
  }
}
```

返回结果字段说明：

- `id`：本次消息的唯一标识符。
- `type`：始终为 `message`。
- `role`：始终为 `assistant`。
- `content`：回复内容数组，每个元素包含 `type`（如 `text`）和对应的内容。
- `model`：处理请求的模型名称。
- `stop_reason`：停止原因。稳定取值包括 `end_turn`、`max_tokens`、`stop_sequence`、`tool_use`、`pause_turn`（可把当前 assistant 内容原样回传以继续）、`refusal` 和 `model_context_window_exceeded`。
- `stop_sequence`：如果因自定义停止序列而停止，显示匹配的停止序列文本。
- `stop_details`：当 `stop_reason` 为 `refusal` 时，可能包含拒绝类别和说明。
- `usage`：token 使用统计。`input_tokens` 是未缓存输入；`cache_creation_input_tokens` 和 `cache_read_input_tokens` 分别是缓存写入与读取；`output_tokens` 是全部输出 token 数。若返回 `output_tokens_details.thinking_tokens`，该值是 `output_tokens` 的子集，计算总量或费用时不要再次相加。该明细没有权威计数时可能为 `null` 或省略。
- `usage.cache_creation`：可选的缓存写入 TTL 明细，包含 `ephemeral_5m_input_tokens` 与 `ephemeral_1h_input_tokens`。对象存在时，两项之和等于 `cache_creation_input_tokens`；字段为 `null` 或省略表示当前响应没有可用的 TTL 拆分，不能按 `0` 解读。
- `usage.cost`：非流式响应可能包含 Ace Data Cloud 记录的额度消耗对象，其中 `amount` 是本次实际消耗、`currency` 是计量单位，`list_amount` 是折扣前金额（如有）。Fable 5.1 的官方缓存读取基价为 $0.25/百万 Token，5 分钟与 1 小时缓存写入基价分别为 $12.50 和 $20/百万 Token；平台实际价格按套餐折扣换算。

## 系统提示词

Claude Messages API 支持通过 `system` 字段设定系统提示词，用于定义模型的行为、角色和上下文。

### Python 示例

```python
import requests

url = "https://api.acedata.cloud/v1/messages"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "system": "你是一位专业的中文翻译助手，请将用户输入的英文翻译成中文。",
    "messages": [
        {"role": "user", "content": "The quick brown fox jumps over the lazy dog."}
    ]
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

通过设置 `system` 提示词，可以精确地控制 Claude 的角色和行为方式。

## 流式响应

该接口也支持流式响应，将 `stream` 参数设为 `true` 即可获得逐步返回的效果，非常适合在网页中实现逐字显示。

### Python 示例

```python
import requests

url = "https://api.acedata.cloud/v1/messages"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "stream": True,
    "messages": [
        {"role": "user", "content": "Hello, Claude"}
    ]
}

response = requests.post(url, json=payload, headers=headers, stream=True)
for line in response.iter_lines():
    if line:
        print(line.decode("utf-8"))
```

流式响应以 Server-Sent Events (SSE) 格式返回，每行以 `event:` 和 `data:` 为前缀。流式事件类型包括：

- `message_start`：消息开始，包含消息的基本信息和模型名称。
- `content_block_start`：内容块开始。
- `content_block_delta`：内容块增量更新，包含新生成的文本片段。
- `content_block_stop`：内容块结束。
- `message_delta`：消息级别的增量更新，包含 `stop_reason` 和最终的 `usage` 信息。`output_tokens_details.thinking_tokens` 的权威值只应从最后一个 `message_delta.usage` 读取，不要跨事件累加。
- `message_stop`：消息结束。

输出效果如下：

```
event: message_start
data: {"type":"message_start","message":{"id":"msg_01XFDUDYJgAACzvnptvVoYEL","type":"message","role":"assistant","content":[],"model":"claude-sonnet-4-20250514","stop_reason":null,"stop_sequence":null,"usage":{"input_tokens":12,"output_tokens":0}}}

event: content_block_start
data: {"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"Hi"}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"! My name is"}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":" Claude. How can I help you today?"}}

event: content_block_stop
data: {"type":"content_block_stop","index":0}

event: message_delta
data: {"type":"message_delta","delta":{"stop_reason":"end_turn","stop_sequence":null},"usage":{"output_tokens":15}}

event: message_stop
data: {"type":"message_stop"}
```

可以看到，流式响应中 `content_block_delta` 事件包含了逐步生成的文本内容，通过拼接所有 `text_delta` 即可获得完整回复。

### JavaScript 示例

```javascript
const options = {
  method: "POST",
  headers: {
    accept: "application/json",
    authorization: "Bearer {token}",
    "content-type": "application/json",
  },
  body: JSON.stringify({
    model: "claude-sonnet-4-20250514",
    max_tokens: 1024,
    stream: true,
    messages: [{ role: "user", content: "Hello, Claude" }],
  }),
};

const response = await fetch("https://api.acedata.cloud/v1/messages", options);
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  console.log(decoder.decode(value));
}
```

## 多轮对话

如果您想要对接多轮对话功能，需要在 `messages` 数组中交替排列 `user` 和 `assistant` 角色的消息，将之前的对话历史一并传入。

### Python 示例

```python
import requests

url = "https://api.acedata.cloud/v1/messages"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "messages": [
        {"role": "user", "content": "Hello, my name is Alice."},
        {"role": "assistant", "content": "Hello Alice! Nice to meet you. How can I help you today?"},
        {"role": "user", "content": "What is my name?"}
    ]
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

返回结果如下：

```json
{
  "id": "msg_01Y1wfQmd89g968TVbFu57Yc",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Your name is Alice, as you just told me!"
    }
  ],
  "model": "claude-sonnet-4-20250514",
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 40,
    "output_tokens": 14
  }
}
```

通过在 `messages` 中传递完整的对话历史，Claude 可以结合上下文进行准确的回答。

## 深度思考模型

Claude 的 thinking 与 thinking summary 是两个不同概念：模型可以进行内部推理，但 API 不会返回原始思维链。需要展示推理过程时，API 返回的是经过处理的摘要。

当前模型建议使用 adaptive thinking，并通过 `output_config.effort` 控制总体推理投入：

```python
import requests

url = "https://api.acedata.cloud/v1/messages"
headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}
payload = {
    "model": "claude-opus-5",
    "max_tokens": 16000,
    "thinking": {
        "type": "adaptive",
        "display": "summarized"
    },
    "output_config": {
        "effort": "high"
    },
    "messages": [
        {"role": "user", "content": "What is the sine of 30 degrees?"}
    ]
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

响应中的 thinking 块形如：

```json
{
  "type": "thinking",
  "thinking": "The problem asks for a standard trigonometric value...",
  "signature": "opaque-signature"
}
```

- `display: "summarized"` 返回可读的思考摘要；它不是原始思维链。
- `display: "omitted"` 返回 `thinking: ""`，但仍保留 opaque `signature` 以支持后续对话。
- Fable 5.1、Fable 5、Opus 5、Sonnet 5、Opus 4.8 和 Opus 4.7 的 display 默认值为 `omitted`；Opus 4.6、Sonnet 4.6 及更早支持 thinking 的模型默认使用 `summarized`。
- Display 只影响返回内容和流式延迟，不关闭推理，也不减少 thinking token 的计费。
- 是否默认启用 thinking 与 display 默认值是两个独立问题。Opus 5、Sonnet 5 默认启用 adaptive thinking；对 Opus 5，省略 `thinking` 等同于 adaptive，省略 `output_config.effort` 等同于 `high`。Opus 4.8、4.7 和 4.6 需要显式启用。
- Thinking 与最终正文共同占用 `max_tokens` 输出预算。预算过小时，thinking 可能占用大部分额度，使正文为空或被截断；请提高 `max_tokens`，或使用 `low` / `medium` effort 控制推理投入。
- 对允许关闭 thinking 的模型，可传 `thinking: {"type":"disabled"}`；disabled 仅能与 `low`、`medium` 或 `high` 搭配，`xhigh` / `max` 会返回 400。
- `budget_tokens` 仅用于仍支持固定思考预算的旧模型。新模型应使用 `thinking.type=adaptive` 和 `output_config.effort`；Fable 5.1 的 thinking 始终开启，不能显式关闭。
- 多轮对话和工具调用时，应将 assistant 返回的完整 thinking 块及 signature 原样传回；不要修改或自行生成 signature。
- 部分兼容路由无法无损处理 `redacted_thinking` 或显式关闭 thinking，此时会返回参数错误，而不会静默丢弃或改变请求语义。

流式请求中，`summarized` 会产生 `thinking_delta`；`omitted` 不产生 `thinking_delta`，只保留 thinking 块生命周期和 `signature_delta`。

## 视觉模型

Claude 支持多模态输入，可以同时处理文本和图像。在 Messages API 中，通过将 `content` 设为数组格式，并传入图像内容块即可使用视觉能力。

### 使用 Base64 编码图像

```python
import base64
import requests

url = "https://api.acedata.cloud/v1/messages"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

# 读取并编码图片
with open("image.png", "rb") as f:
    image_data = base64.standard_b64encode(f.read()).decode("utf-8")

payload = {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_data
                    }
                },
                {
                    "type": "text",
                    "text": "What's in this image?"
                }
            ]
        }
    ]
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

### 使用 URL 图像

```python
import requests

url = "https://api.acedata.cloud/v1/messages"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "url",
                        "url": "https://cdn.acedata.cloud/ueugot.png"
                    }
                },
                {
                    "type": "text",
                    "text": "What's in this image?"
                }
            ]
        }
    ]
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

### cURL 示例

```bash
curl -X POST 'https://api.acedata.cloud/v1/messages' \
  -H 'accept: application/json' \
  -H 'authorization: Bearer {token}' \
  -H 'content-type: application/json' \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "image",
            "source": {
              "type": "url",
              "url": "https://cdn.acedata.cloud/ueugot.png"
            }
          },
          {
            "type": "text",
            "text": "What'\''s in this image?"
          }
        ]
      }
    ]
  }'
```

支持的图片格式包括：`image/jpeg`、`image/png`、`image/gif`、`image/webp`。

## 文档与 PDF

PDF 使用 `document` 内容块，支持 Base64 与 URL 两种稳定来源。Base64 来源必须使用 `application/pdf`：

```python
import base64

with open("report.pdf", "rb") as f:
    pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")

payload = {
    "model": "claude-fable-5-1",
    "max_tokens": 1024,
    "messages": [{
        "role": "user",
        "content": [
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": pdf_data
                },
                "title": "Quarterly report"
            },
            {"type": "text", "text": "Summarize this PDF."}
        ]
    }]
}
```

URL 来源写作 `{"type":"url","url":"https://example.com/report.pdf"}`。`document` 还支持 `text/plain` 与由 text/image 块组成的 `content` 来源；可选字段包括 `title`、`context` 和 `citations`。Files API 的 `file_id` 来源属于独立 beta 功能，不在本接口的稳定契约内。

## 提示缓存

顶层 `cache_control` 会自动把缓存断点放在最后一个可缓存块上：

```python
payload = {
    "model": "claude-fable-5-1",
    "max_tokens": 1024,
    "cache_control": {"type": "ephemeral", "ttl": "5m"},
    "system": "You are an expert on this reference material.",
    "messages": [{"role": "user", "content": "Summarize the key points."}]
}
```

需要精确控制位置时，也可把同样的 `cache_control` 写在 text、image、document、tool_use、tool_result 内容块或工具定义上。`ttl` 支持 `5m`（默认）与 `1h`；请通过 `usage.cache_creation_input_tokens` 和 `usage.cache_read_input_tokens` 判断缓存写入与命中。

当响应提供 `usage.cache_creation` 时，`ephemeral_5m_input_tokens + ephemeral_1h_input_tokens = cache_creation_input_tokens`。若 `cache_creation` 为 `null` 或省略，表示只有缓存写入总量、没有权威 TTL 拆分；此时不要将任一 bucket 当作已知的 0，计费和总量仍以 aggregate 字段为准。

返回结果示例：

```json
{
  "id": "msg_01NCrxpZmV17bhQJJRQEFEb9",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "This image shows an API request configuration interface for what appears to be an AI chat completion service. The interface includes parameters for model selection, messages, stream mode, and max tokens settings."
    }
  ],
  "model": "claude-sonnet-4-20250514",
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 1570,
    "output_tokens": 52
  }
}
```

## 工具调用（Tool Use）

Claude Messages API 原生支持工具调用功能，允许模型在需要时调用您预定义的工具/函数。

### Python 示例

```python
import requests

url = "https://api.acedata.cloud/v1/messages"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "tools": [
        {
            "name": "get_weather",
            "description": "Get the current weather in a given location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA"
                    }
                },
                "required": ["location"]
            }
        }
    ],
    "messages": [
        {"role": "user", "content": "What's the weather like in San Francisco?"}
    ]
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

当模型决定调用工具时，返回结果中 `content` 会包含 `tool_use` 类型的内容块：

```json
{
  "id": "msg_01Aq9w938a90dw8q",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Let me check the weather in San Francisco for you."
    },
    {
      "type": "tool_use",
      "id": "toolu_01A09q90qw90lq917835lgs",
      "name": "get_weather",
      "input": {
        "location": "San Francisco, CA"
      }
    }
  ],
  "model": "claude-sonnet-4-20250514",
  "stop_reason": "tool_use",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 120,
    "output_tokens": 68
  }
}
```

注意 `stop_reason` 为 `tool_use`，表示模型需要调用工具。收到该结果后，您需要执行工具函数并将结果以 `tool_result` 的形式回传给模型：

```python
payload = {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "tools": [
        {
            "name": "get_weather",
            "description": "Get the current weather in a given location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA"
                    }
                },
                "required": ["location"]
            }
        }
    ],
    "messages": [
        {"role": "user", "content": "What's the weather like in San Francisco?"},
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Let me check the weather in San Francisco for you."},
                {"type": "tool_use", "id": "toolu_01A09q90qw90lq917835lgs", "name": "get_weather", "input": {"location": "San Francisco, CA"}}
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_01A09q90qw90lq917835lgs",
                    "content": "Sunny, 72°F"
                }
            ]
        }
    ]
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

模型会基于工具返回的结果，生成最终的自然语言回复。

## 与 Chat Completion API 的区别

Ace Data Cloud 同时提供两种 Claude API 格式，两者的主要区别如下：

Messages API 的 `usage.input_tokens` 仅表示未缓存输入，`cache_read_input_tokens` 与 `cache_creation_input_tokens` 是独立计费分桶；三者会分别按对应价格计算。

| 特性       | Messages API (`/v1/messages`)    | Chat Completion API (`/v1/chat/completions`) |
| ---------- | -------------------------------- | -------------------------------------------- |
| 格式       | Anthropic 原生格式               | OpenAI 兼容格式                              |
| 系统提示词 | 独立的 `system` 字段             | 通过 `messages` 中 `role: "system"` 传递     |
| 响应结构   | `content` 数组（支持多种类型）   | `choices` 数组（包含 `message`）             |
| 流式格式   | SSE 事件（多种事件类型）         | SSE `data` 行                                |
| 深度思考   | 原生 `thinking` 与 `output_config.effort` | 模型默认策略与兼容参数                       |
| 工具调用   | 原生 `tools` + `input_schema`    | OpenAI 兼容的 `tools` 格式                   |
| Token 统计 | `output_tokens_details.thinking_tokens` | `completion_tokens_details.reasoning_tokens` |

如果您的系统已经对接了 OpenAI 格式的 API，可以使用 Chat Completion API 来无缝切换。如果您需要使用 Claude 的全部原生能力，建议使用 Messages API。

## 错误处理

公开接口的错误响应使用 Ace Data Cloud 平台 envelope：`error.code` 是稳定错误码，`error.message` 是说明，`trace_id` 用于排查请求。常见 HTTP 状态包括：

- `400`：请求参数或协议内容无效。
- `401`：授权令牌无效、缺失或过期。
- `403`：禁止访问、余额不足或配额受限。
- `404`：API 或模型不存在。
- `413`：请求体过大。
- `429`：请求过多。
- `500` / `503` / `504`：服务错误、暂时不可用或处理超时。

### 错误响应示例

```json
{
  "error": {
    "code": "api_error",
    "message": "fetch failed"
  },
  "trace_id": "2cf86e86-22a4-46e1-ac2f-032c0f2a4e89"
}
```

该错误结构是 Ace Data Cloud 的运行时契约，不等同于 Anthropic 官方错误 envelope；请按 HTTP 状态与 `error.code` 处理。

## 结论

通过本文档，您已经了解了如何使用 Claude Messages API 以 Anthropic 原生格式调用 Claude 的对话功能。Messages API 支持基本对话、系统提示词、流式响应、多轮对话、深度思考、视觉理解、PDF、提示缓存和工具调用等丰富功能。如有任何问题，请随时联系我们的技术支持团队。
