# Kimi Chat Completion API 申请及使用

Kimi 是月之暗面推出的 AI 模型系列。当前推荐的 `kimi-k3` 面向长程编程、Agent、复杂推理和知识工作，可通过 OpenAI 兼容的 Chat Completions API 调用。

本文档主要介绍 Kimi Chat Completion API 操作的使用流程，利用它我们可以轻松使用官方 Kimi 的对话功能。

## 申请流程

要使用 Kimi Chat Completion API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Kimi Chat Completion API →](https://platform.acedata.cloud/documents/kimi-chat-completions)

## 基本使用

接下来就可以在界面上填写对应的内容，如图所示：

<p><img src="https://cdn.acedata.cloud/ej5ozg.png" width="400" class="m-auto"></p>

第一次使用该接口时，至少需要填写三个内容：`authorization` 可直接从下拉列表选择；`model` 用于选择 Kimi 模型，推荐使用 `kimi-k3`；`messages` 是对话消息数组，每条消息包含 `role` 和 `content`，其中 `role` 支持 `user`、`assistant`、`system` 和 `tool`。

同时您可以注意到右侧有对应的调用代码生成，您可以复制代码直接运行，也可以直接点击「Try」按钮进行测试。

<p><img src="https://cdn.acedata.cloud/six7e3.png" width="400" class="m-auto"></p>

以下是使用 `reasoning_effort: max` 获得的真实 K3 响应（省略未使用的扩展字段）：

```json
{
  "id": "msg_2D4Btbg1WgvkNE3tCYkR4xGA",
  "object": "chat.completion",
  "created": 1784466588,
  "model": "kimi-k3",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 86,
    "completion_tokens": 206,
    "total_tokens": 292
  }
}
```

返回结果一共有多个字段，介绍如下：

- `id`，生成此次对话任务的 ID，用于唯一标识此次对话任务。
- `model `，选择的 Kimi 官网模型。
- `choices`Kimi 针对提问词给于的回答信息。
- `usage `：针对本次问答对 token 的统计信息。

其中 `choices` 是包含了 Kimi 的回答信息，它里面的 `choices` 是 Kimi回答的具体信息，可以发现如图所示。

<p><img src="https://cdn.acedata.cloud/tv9rul.png" width="400" class="m-auto"></p>

可以看到，`choices` 里面的 `content` 字段包含了 Kimi 回复的具体内容；K3 还可能返回 `reasoning_content`，用于表示推理过程。

## K3 推理强度

`kimi-k3` 始终启用推理。请求体顶层支持 `reasoning_effort` 字段，当前唯一受支持的值是 `max`；省略该字段时同样使用 `max`。`standard`、`high` 或其他字符串可能被部分兼容上游宽松接受，但不保证改变推理行为，请勿依赖。

```bash
curl https://api.acedata.cloud/kimi/chat/completions \
  -H "Authorization: Bearer $ACEDATACLOUD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kimi-k3",
    "messages": [{"role": "user", "content": "审查这段代码并给出修复方案"}],
    "reasoning_effort": "max"
  }'
```

使用 OpenAI SDK 时可直接传递该字段：

```python
response = client.chat.completions.create(
    model="kimi-k3",
    messages=[{"role": "user", "content": "设计一个可靠的任务队列"}],
    reasoning_effort="max",
)
```

多轮对话和工具调用时，请将上一轮完整的 assistant 消息回传到 `messages`，包括 `reasoning_content` 和 `tool_calls`。

### 官方参考

- [Thinking Effort](https://platform.kimi.ai/docs/guide/use-thinking-effort)：说明 Kimi K3 始终启用推理，当前 `reasoning_effort` 唯一支持的值为 `max`。
- [Model Parameter Reference](https://platform.kimi.ai/docs/api/models-overview)：对比 K3 与 K2 系列的推理参数、上下文窗口和工具调用差异。
- [Create Chat Completion](https://platform.kimi.ai/docs/api/chat)：Moonshot 官方 Chat Completions 请求、响应和 OpenAPI 字段定义。

## 流式响应

该接口也支持流式响应，这对网页对接十分有用，可以让网页实现逐字显示效果。

如果想流式返回响应，可以更改请求头里面的 `stream ` 参数，修改为 `true`。

修改如图所示，不过调用代码需要有对应的更改才能支持流式响应。

<p><img src="https://cdn.acedata.cloud/a3nzpw.png" width="400" class="m-auto"></p>

将 `stream` 修改为 `true` 之后，API 将逐行返回对应的 JSON 数据，在代码层面我们需要做相应的修改来获得逐行的结果。

Python 样例调用代码：

```python
import requests

url = "https://api.acedata.cloud/kimi/chat/completions"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "model": "kimi-k3",
    "messages": [{"role":"user","content":"Hello"}],
    "reasoning_effort": "max",
    "stream": True
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

下面节选同一次真实 K3 Max 流式响应中的起始、推理、正文、结束和用量数据块：

```json
data: {"id":"msg_er7WZjyv2kD3TG2yzbFPu5ZJ","object":"chat.completion.chunk","created":1784466598,"model":"kimi-k3","choices":[{"index":0,"delta":{"content":"","role":"assistant"},"finish_reason":null}],"usage":null}

data: {"id":"msg_er7WZjyv2kD3TG2yzbFPu5ZJ","object":"chat.completion.chunk","created":1784466598,"model":"kimi-k3","choices":[{"index":0,"delta":{"reasoning_content":"The"},"finish_reason":null}],"usage":null}

data: {"id":"msg_er7WZjyv2kD3TG2yzbFPu5ZJ","object":"chat.completion.chunk","created":1784466598,"model":"kimi-k3","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}],"usage":null}

data: {"id":"msg_er7WZjyv2kD3TG2yzbFPu5ZJ","object":"chat.completion.chunk","created":1784466598,"model":"kimi-k3","choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":null}

data: {"id":"msg_er7WZjyv2kD3TG2yzbFPu5ZJ","object":"chat.completion.chunk","created":1784466598,"model":"kimi-k3","choices":[],"usage":{"prompt_tokens":172,"completion_tokens":168,"total_tokens":340}}

data: [DONE]
```

可以看到，响应里面有许多 `data` ，`data` 里面的 `choices` 即为最新的回答内容，与上文介绍的内容一致。`choices` 是新增的回答内容，您可以根据结果来对接到您的系统中。同时流式响应的结束是根据 `data` 的内容来判断的，如果内容为 `[DONE]`，则表示流式响应回答已经全部结束。返回的 `data` 结果一共有多个字段，介绍如下：

- `id`，生成此次对话任务的 ID，用于唯一标识此次对话任务。
- `model `，选择的 Kimi 官网模型。
- `choices`，Kimi 针对提问词给于的回答信息。

JavaScript 也是支持的，比如 Node.js 的流式调用代码如下：

```javascript
const options = {
  method: "POST",
  headers: {
    accept: "application/json",
    authorization: "Bearer {token}",
    "content-type": "application/json"
  },
  body: JSON.stringify({
    model: "kimi-k3",
    messages: [{ role: "user", content: "Hello" }],
    stream: true
  })
};

const response = await fetch("https://api.acedata.cloud/kimi/chat/completions", options);
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
jsonObject.put("model", "kimi-k3");
jsonObject.put("messages", new JSONArray().put(new JSONObject().put("role", "user").put("content", "Hello")));
jsonObject.put("stream", true);
MediaType mediaType = MediaType.parse("application/json; charset=utf-8");
RequestBody body = RequestBody.create(jsonObject.toString(), mediaType);
Request request = new Request.Builder()
  .url("https://api.acedata.cloud/kimi/chat/completions")
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

如果您想要对接多轮对话功能，需要对 `messages` 字段上传多个提问词，多个提问词的具体示例如下图所示：

<p><img src="https://cdn.acedata.cloud/g85v2a.png" width="400" class="m-auto"></p>

Python 样例调用代码：

```python
import requests

url = "https://api.acedata.cloud/kimi/chat/completions"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "model": "kimi-k3",
    "messages": [{"role":"assistant","content":"Hello! How can I help you today?"},{"role":"user","content":"What model are you?"}],
    "reasoning_effort": "max"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

通过上传多个提问词，就可以轻松实现多轮对话。以下是该请求获得的真实 K3 Max 响应（省略未使用的扩展字段）：

```json
{
  "id": "msg_Rqp8nPGBDHWwBlL4VpxuafOp",
  "object": "chat.completion",
  "created": 1784466628,
  "model": "kimi-k3",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "I’m Kimi, an AI assistant developed by Moonshot AI (月之暗面). I don’t have a specific public model version identifier to share from here."
      },
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 134,
    "completion_tokens": 346,
    "total_tokens": 480
  }
}
```

可以看到，`choices` 包含的信息与基本使用的内容是一致的，这个包含了 Kimi 针对多个对话进行回复的具体内容，这样就可以根据多个对话内容来回答对应的问题了。

## 错误处理

在调用 API 时，如果遇到错误，API 会返回相应的错误代码和信息。例如：

- `400 token_mismatched`：Bad request, possibly due to missing or invalid parameters.
- `400 api_not_implemented`：Bad request, possibly due to missing or invalid parameters.
- `401 invalid_token`：Unauthorized, invalid or missing authorization token.
- `429 too_many_requests`：Too many requests, you have exceeded the rate limit.
- `500 api_error`：Internal server error, something went wrong on the server.

### 错误响应示例

```
{
  "success": false,
  "error": {
    "code": "api_error",
    "message": "fetch failed"
  },
  "trace_id": "2cf86e86-22a4-46e1-ac2f-032c0f2a4e89"
}
```

## 结论

通过本文档，您已经了解了如何使用 Kimi Chat Completion API 实现普通对话、流式响应、多轮对话，以及通过 `reasoning_effort` 控制 K3 的推理强度。
