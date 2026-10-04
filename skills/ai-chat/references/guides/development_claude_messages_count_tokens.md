# Claude Messages Count Tokens API 申请及使用

Claude Messages Count Tokens API 可以在不实际创建消息的情况下，计算一条 Message 的输入 Token 数量，包括工具、图片和文档等内容的 Token 计数。这在需要预估成本或检查输入是否超出模型上下文限制时非常有用。

本文档主要介绍 Claude Messages Count Tokens API 的使用流程。

## 申请流程

要使用 Claude Messages Count Tokens API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Claude Messages Count Tokens API →](https://platform.acedata.cloud/documents/claude-messages-count-tokens)

## 基本使用

Claude Messages Count Tokens API 的请求路径为 `/v1/messages/count_tokens`，与 Anthropic 官方 API 保持一致。我们至少需要提供两个必填参数：

- `model`：选择使用的 Claude 模型；`claude-opus-5-5` 可用于 Messages Token Count，如最新旗舰 `claude-fable-5-1`；原 `claude-fable-5` 仍兼容保留。 `claude-sonnet-5-5` 已加入原生 Messages 系列接口，支持图像输入和自适应思考；其输入、输出和缓存读取官方参考价分别为每百万 Token 2、10 和 0.20 美元。
- `messages`：输入的消息数组，每条消息包含 `role`（角色）和 `content`（内容）。

常用可选参数：

- `system`：系统提示词，会计入 Token 数量。
- `tools`：工具定义，会计入 Token 数量。
- `thinking`：扩展思考配置。
- `tool_choice`：工具选择配置。
- `cache_control`：顶层或内容块级缓存控制配置。

`messages`、`system`、工具调用回放、URL 图片和 document/PDF 内容块使用与 Messages API 相同的稳定请求结构。

### cURL 示例

```bash
curl -X POST 'https://api.acedata.cloud/v1/messages/count_tokens' \
  -H 'accept: application/json' \
  -H 'authorization: Bearer {token}' \
  -H 'content-type: application/json' \
  -d '{
    "model": "claude-fable-5-1",
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
import httpx

url = "https://api.acedata.cloud/v1/messages/count_tokens"
headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json",
}
payload = {
    "model": "claude-fable-5-1",
    "messages": [
        {
            "role": "user",
            "content": "Hello, Claude"
        }
    ],
}
response = httpx.post(url, headers=headers, json=payload)
print(response.json())
```

返回结果示例：

```json
{
  "input_tokens": 11
}
```

### 使用 Anthropic SDK

Claude Messages Count Tokens API 接受 Anthropic SDK 的稳定请求结构，可以通过 `anthropic` 库调用。接口使用所选模型对应的原生 Count Tokens 能力统计输入，可用于在发送 Messages 请求前检查输入规模。

```python
from anthropic import Anthropic

client = Anthropic(
    api_key="{token}",
    base_url="https://api.acedata.cloud",
)

result = client.messages.count_tokens(
    model="claude-opus-4-8",
    messages=[
        {
            "role": "user",
            "content": "Hello, Claude"
        }
    ],
)
print(result.input_tokens)
```

## 包含工具的 Token 计数

如果你的请求中包含工具定义，这些工具也会计入 Token 数量：

```python
result = client.messages.count_tokens(
    model="claude-opus-4-8",
    messages=[
        {
            "role": "user",
            "content": "What is the weather in San Francisco?"
        }
    ],
    tools=[
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
)
print(result.input_tokens)
```

## 包含系统提示词的 Token 计数

系统提示词也会计入 Token 数量：

```python
result = client.messages.count_tokens(
    model="claude-opus-4-8",
    system="You are a helpful assistant that speaks Chinese.",
    messages=[
        {
            "role": "user",
            "content": "Hello"
        }
    ],
)
print(result.input_tokens)
```

## 注意事项

- 该 API 仅计算输入 Token 数量，不会产生任何模型输出。
- Token 计数结果可用于预估输入规模和检查上下文窗口；最终计费以实际 Messages 响应中的 `usage` 为准。
- 图片、PDF、工具定义、系统提示词和 thinking 配置会按照所选模型的输入规则计入结果。
- 该 API 完全免费，不消耗任何额度。
