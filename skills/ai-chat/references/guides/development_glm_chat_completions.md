# GLM Chat Completion API 申请及使用

GLM（General Language Model）是智谱 AI（Zhipu AI / Z.ai）推出的新一代大语言模型系列，具备强大的中英文理解与生成能力，在中文场景、代码生成、推理与多轮对话等任务上都有出色表现。GLM-5.3、GLM-5.2、GLM-4.7 等新一代模型在长上下文、工具调用与代码任务上做了大量优化，可广泛应用于智能问答、内容创作、代码辅助、客服机器人等场景。

本文档主要介绍 GLM Chat Completion API 的使用流程，利用它您可以通过统一的 OpenAI 兼容接口轻松调用 GLM 系列模型。

## 申请流程

要使用 GLM Chat Completion API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[GLM Chat Completion API →](https://platform.acedata.cloud/documents/glm-chat-completions)

## 基本使用

GLM Chat Completion API 的请求地址为 `https://api.acedata.cloud/glm/chat/completions`，使用 Bearer Token 鉴权，请求体兼容 OpenAI Chat Completions 协议。

在第一次使用该接口时，我们至少需要填写三个内容：

- `authorization`：直接在下拉列表里面选择 Bearer Token 即可。
- `model`：选择要调用的 GLM 模型，目前支持的模型包括：
  - `glm-5.3`：最新旗舰模型，支持 1M 上下文与最长 128K 输出，适合复杂推理、代码与 Agent 任务。推理始终开启，可通过 `reasoning_effort` 选择 `low`、`high` 或 `max`。
  - `glm-5.2`：上一代旗舰模型，综合能力强。
  - `glm-5.1`：成熟旗舰模型，适合通用复杂任务。
  - `glm-4.7`：在推理、工具调用与代码任务上表现优秀。
  - `glm-4.6`：通用对话模型，平衡效果与成本。
  - `glm-3-turbo`：经典对话模型，适用于一般文本生成任务。
- `messages`：提示词数组，每条消息包含 `role` 和 `content`，`role` 支持 `user`、`assistant`、`system` 三种角色。

常用可选参数：

- `max_tokens`：限制单次回复的最大 token 数。
- `temperature`：生成随机性，0-2 之间，值越大越发散。
- `top_p`：核采样参数，控制候选 token 的累积概率阈值。
- `n`：一次生成多少条候选回复。
- `stream`：是否启用流式响应，默认 `false`。
- `stop`：自定义停止序列。

下面是一个最简单的 Python 调用示例：

```python
import requests

url = "https://api.acedata.cloud/glm/chat/completions"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "model": "glm-5.2",
    "messages": [
        {"role": "user", "content": "hello"}
    ]
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

调用之后，我们发现返回结果如下：

```json
{
  "id": "msg_202604262252030313862701a04e33",
  "model": "glm-5.2",
  "object": "chat.completion",
  "created": 1777215124,
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! 👋 How can I assist you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 23,
    "total_tokens": 33
  }
}
```

返回结果各主要字段说明如下：

- `id`：本次对话任务的唯一 ID。
- `created`：本次对话任务的创建时间（Unix 时间戳，秒）。
- `model`：实际调用的 GLM 模型名称。
- `choices`：模型生成的回复列表。`choices[i].message.content` 即模型回复的具体文本，`finish_reason` 标识结束原因（`stop`、`length`、`tool_calls`、`content_filter` 等）。
- `usage`：本次请求的 token 用量统计，包含 `prompt_tokens`、`completion_tokens`、`total_tokens`。

## 流式响应

该接口支持流式响应（Server-Sent Events），这对网页对接十分有用，可以让网页实现逐字显示效果。

如果想流式返回响应，将请求体中的 `stream` 参数设置为 `true` 即可。

Python 样例调用代码：

```python
import requests

url = "https://api.acedata.cloud/glm/chat/completions"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "model": "glm-4.7",
    "messages": [{"role": "user", "content": "hi"}],
    "stream": True
}

response = requests.post(url, json=payload, headers=headers, stream=True)
for line in response.iter_lines():
    if line:
        print(line.decode("utf-8"))
```

输出效果如下（节选）：

```text
data: {"id": "msg_2026042622521271f765bbc3734ce1", "object": "chat.completion.chunk", "created": 1777215133, "model": "glm-4.7", "choices": [{"delta": {"content": "", "role": "assistant"}, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "msg_2026042622521271f765bbc3734ce1", "object": "chat.completion.chunk", "created": 1777215133, "model": "glm-4.7", "choices": [{"delta": {"content": "你好！有什么我可以"}, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "msg_2026042622521271f765bbc3734ce1", "object": "chat.completion.chunk", "created": 1777215133, "model": "glm-4.7", "choices": [{"delta": {"content": "帮助你的"}, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "msg_2026042622521271f765bbc3734ce1", "object": "chat.completion.chunk", "created": 1777215133, "model": "glm-4.7", "choices": [{"delta": {"content": "吗？"}, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "msg_2026042622521271f765bbc3734ce1", "object": "chat.completion.chunk", "created": 1777215133, "model": "glm-4.7", "choices": [{"delta": {}, "finish_reason": "stop", "index": 0}], "usage": null}

data: {"id": "msg_2026042622521271f765bbc3734ce1", "object": "chat.completion.chunk", "created": 1777215133, "model": "glm-4.7", "choices": [], "usage": {"prompt_tokens": 1420, "completion_tokens": 18, "total_tokens": 1438}}

data: [DONE]
```

可以看到，响应里面有许多 `data`，每条 `data` 包含一个增量片段。`choices[i].delta.content` 是当前 chunk 新增的文本片段，您可以将这些片段拼接起来形成完整回复。当 `data` 内容为 `[DONE]` 时表示流式响应结束。最后一条带 `usage` 的 chunk 会汇总本次请求的 token 用量。

JavaScript（Node.js）样例：

```javascript
const options = {
  method: "POST",
  headers: {
    accept: "application/json",
    authorization: "Bearer {token}",
    "content-type": "application/json"
  },
  body: JSON.stringify({
    model: "glm-4.7",
    messages: [{ role: "user", content: "hi" }],
    stream: true
  })
};

const response = await fetch("https://api.acedata.cloud/glm/chat/completions", options);
const reader = response.body.getReader();
const decoder = new TextDecoder("utf-8");
while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  process.stdout.write(decoder.decode(value));
}
```

Java 样例代码：

```java
JSONObject jsonObject = new JSONObject();
jsonObject.put("model", "glm-4.7");
jsonObject.put("messages", new JSONArray().put(new JSONObject().put("role", "user").put("content", "hi")));
jsonObject.put("stream", true);
MediaType mediaType = MediaType.parse("application/json; charset=utf-8");
RequestBody body = RequestBody.create(jsonObject.toString(), mediaType);
Request request = new Request.Builder()
  .url("https://api.acedata.cloud/glm/chat/completions")
  .post(body)
  .addHeader("accept", "application/json")
  .addHeader("authorization", "Bearer {token}")
  .addHeader("content-type", "application/json")
  .build();

OkHttpClient client = new OkHttpClient();
Response response = client.newCall(request).execute();
System.out.println(response.body().string());
```

其他语言可以另外自行改写，原理都是一样的。

## 多轮对话

如果您想要实现多轮对话功能，需要将历史对话依次放入 `messages` 数组，并保留 `user` 与 `assistant` 交替出现的顺序。

Python 样例调用代码：

```python
import requests

url = "https://api.acedata.cloud/glm/chat/completions"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "model": "glm-4.7",
    "messages": [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi! How can I assist you today?"},
        {"role": "user", "content": "What did I say just now?"}
    ]
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

通过上传多个提问词，就可以轻松实现多轮对话，可以得到如下回答：

```json
{
  "id": "msg_20260426225208b95324e9945a48d3",
  "model": "glm-4.7",
  "object": "chat.completion",
  "created": 1777215128,
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "You said: **\"Hello\"** 😊\n\nLet me know if you need anything else!"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 48,
    "completion_tokens": 37,
    "total_tokens": 85
  }
}
```

可以看到，`choices` 包含的信息与基本使用一致，模型基于完整的对话历史给出回复，从而支持多轮上下文交互。

## 系统提示词（System Prompt）

可以在 `messages` 的开头添加一条 `role` 为 `system` 的消息，用来约束模型的角色、风格或行为：

```python
payload = {
    "model": "glm-4.7",
    "messages": [
        {"role": "system", "content": "你是一名资深的中文写作助手，请用简洁专业的语气回复。"},
        {"role": "user", "content": "请用三句话介绍一下 GLM 模型。"}
    ]
}
```

## 工具调用（Function Calling）

GLM 模型支持 OpenAI 兼容的 Function Calling，可以通过 `tools` 参数声明可调用的函数，模型在需要时会在 `choices[i].message.tool_calls` 中返回结构化的函数调用信息。

```python
payload = {
    "model": "glm-4.7",
    "messages": [
        {"role": "user", "content": "北京今天天气怎么样？"}
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "查询指定城市的天气",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "城市名称"}
                    },
                    "required": ["city"]
                }
            }
        }
    ]
}
```

模型如果决定调用工具，返回结果中 `finish_reason` 会变为 `tool_calls`，并在 `message.tool_calls` 中给出函数名和 JSON 字符串形式的参数。您可以执行该函数并将结果作为 `role` 为 `tool` 的消息回传给模型，从而完成完整的工具调用回路。

## 模型选择建议

| 模型           | 适用场景                                       |
| -------------- | ---------------------------------------------- |
| `glm-5.3`      | 最新旗舰，1M 上下文、最长 128K 输出，推荐用于复杂推理、代码与 Agent 任务 |
| `glm-5.2`      | 上一代旗舰，适合复杂推理、代码与 Agent 任务    |
| `glm-5.1`      | 成熟旗舰，适合复杂推理、长文档分析             |
| `glm-4.7`      | 工具调用、代码生成、Agent 编排等任务           |
| `glm-4.6`      | 通用对话、内容创作的均衡选择                   |
| `glm-3-turbo`  | 一般文本生成任务，对成本敏感的场景             |

## 错误处理

在调用 API 时，如果遇到错误，API 会返回相应的错误代码和信息。例如：

- `400 token_mismatched`：请求参数缺失或无效。
- `400 api_not_implemented`：使用了不被支持的参数或模型。
- `401 invalid_token`：未授权，Bearer Token 缺失或失效。
- `429 too_many_requests`：触发频率限制，请稍后重试。
- `500 api_error`：服务器内部错误或上游暂时不可用。

### 错误响应示例

```json
{
  "trace_id": "69ea9bcf-c5da-41a3-be97-c80912a08523",
  "error": {
    "code": "api_error",
    "message": "Service is temporarily unavailable, please retry later."
  }
}
```

当返回 `api_error` 且消息为 `Service is temporarily unavailable, please retry later.` 时，通常表示上游 GLM 服务暂时不可用，建议带指数退避重试，或切换到其他可用的 GLM 模型（例如从 `glm-5.1` 临时切换到 `glm-4.7` 或 `glm-4.6`）。

## 结论

通过本文档，您已经了解了如何使用 GLM Chat Completion API 调用智谱 AI 的 GLM 系列模型，包括基本调用、流式响应、多轮对话、系统提示词与工具调用等典型用法。希望本文档能帮助您更好地对接和使用该 API。如有任何问题，请随时联系我们的技术支持团队。
