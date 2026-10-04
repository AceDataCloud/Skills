# Grok Chat Completion API 申请及使用

xAI Grok 是一款非常强大的 AI 对话系统，只要输入提示词，就能在短短几秒内生成流畅自然的回复。Grok 以其独特的幽默风格和实时网络信息获取能力在业界独树一帜，如今，Grok 已在多个创新领域崭露头角，其影响力正快速扩大。无论是日常对话、创意写作，还是技术分析、代码调试，Grok 都能提供富有洞察力的智能协助，为用户的决策和创作带来全新维度的支持。

本文档主要介绍 Grok Chat Completion API 操作的使用流程，利用它我们可以轻松使用官方 Grok 的对话功能。

## 申请流程

要使用 Grok Chat Completion API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Grok Chat Completion API →](https://platform.acedata.cloud/documents/grok-chat-completions)

## 基本使用

接下来就可以在界面上填写对应的内容，如图所示：

<p><img src="https://cdn.acedata.cloud/vunnjf.png" width="400" class="m-auto"></p>

在第一次使用该接口时，我们至少需要填写三个内容，一个是 `authorization`，直接在下拉列表里面选择即可。另一个参数是 `model`， `model` 就是我们选择使用 Grok 官网模型类别，这里我们主要有 8 种模型，详情可以看我们提供的模型。最后一个参数是`messages`，`messages`是我们输入的提问词数组，它是一个数组，表示可以同时上传多个提问词，每个提问词包含了 `role` 和 `content`，其中 `role` 表示提问者的角色，我们提供了三种身份，分别为 `user` 、`assistant`、`system` 。另一个 `content` 就是我们提问的具体内容。

同时您可以注意到右侧有对应的调用代码生成，您可以复制代码直接运行，也可以直接点击「Try」按钮进行测试。

常用可选参数：

- `max_tokens`：限制单次回复的最大 token 数。
- `temperature`：生成随机性，0-2 之间，值越大越发散。
- `n`：一次生成多少条候选回复。

<p><img src="https://cdn.acedata.cloud/d7iwun.png" width="400" class="m-auto"></p>

调用之后，我们发现返回结果如下：

```json
{
  "id": "foaicmpl-13936918-cb99-49e1-b94c-bde98b482ed4",
  "model": "grok-4",
  "object": "chat.completion",
  "created": 1755839683,
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Yo! What's up? 😎 Ready to dive into whatever you're pondering about today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 8,
    "completion_tokens": 20,
    "total_tokens": 28,
    "prompt_tokens_details": {
      "cached_tokens": 0,
      "text_tokens": 0,
      "audio_tokens": 0,
      "image_tokens": 0
    },
    "completion_tokens_details": {
      "text_tokens": 0,
      "audio_tokens": 0,
      "reasoning_tokens": 0
    },
    "input_tokens": 0,
    "output_tokens": 0,
    "input_tokens_details": null
  }
}
```

返回结果一共有多个字段，介绍如下：

- `id`，生成此次对话任务的 ID，用于唯一标识此次对话任务。
- `model `，选择的 Grok 官网模型。
- `choices`，Grok 针对提问词给于的回答信息。
- `usage `：针对本次问答对 token 的统计信息。

其中 `choices` 是包含了 Grok 的回答信息，它里面的 `choices` 是 Grok回答的具体信息，可以发现如图所示。

<p><img src="https://cdn.acedata.cloud/p8vupk.png" width="400" class="m-auto"></p>

可以看到，`choices` 里面的 `content` 字段包含了 Grok 回复的具体内容。

## 流式响应

该接口也支持流式响应，这对网页对接十分有用，可以让网页实现逐字显示效果。

如果想流式返回响应，可以更改请求头里面的 `stream ` 参数，修改为 `true`。

修改如图所示，不过调用代码需要有对应的更改才能支持流式响应。

<p><img src="https://cdn.acedata.cloud/k883qa.png" width="400" class="m-auto"></p>

将 `stream` 修改为 `true` 之后，API 将逐行返回对应的 JSON 数据，在代码层面我们需要做相应的修改来获得逐行的结果。

Python 样例调用代码：

```python
import requests

url = "https://api.acedata.cloud/grok/chat/completions"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "model": "grok-3",
    "messages": [{"role":"user","content":"Hello"}],
    "stream": True
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

输出效果如下：

```json
data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": null, "choices": [{"delta": {"role": "assistant"}, "logprobs": null, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": null, "choices": [{"delta": {"content": "Yo, "}, "logprobs": null, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": null, "choices": [{"delta": {"content": "what"}, "logprobs": null, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": null, "choices": [{"delta": {"content": "'s g"}, "logprobs": null, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": null, "choices": [{"delta": {"content": "ood?"}, "logprobs": null, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": null, "choices": [{"delta": {"content": " Rea"}, "logprobs": null, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": null, "choices": [{"delta": {"content": "dy t"}, "logprobs": null, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": null, "choices": [{"delta": {"content": "o di"}, "logprobs": null, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": null, "choices": [{"delta": {"content": "ve i"}, "logprobs": null, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": null, "choices": [{"delta": {"content": "nto "}, "logprobs": null, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": null, "choices": [{"delta": {"content": "what"}, "logprobs": null, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": null, "choices": [{"delta": {"content": "ever"}, "logprobs": null, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": null, "choices": [{"delta": {"content": " you"}, "logprobs": null, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": null, "choices": [{"delta": {"content": "'re "}, "logprobs": null, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": null, "choices": [{"delta": {"content": "pond"}, "logprobs": null, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": null, "choices": [{"delta": {"content": "erin"}, "logprobs": null, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": null, "choices": [{"delta": {"content": "g ab"}, "logprobs": null, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": null, "choices": [{"delta": {"content": "out "}, "logprobs": null, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": null, "choices": [{"delta": {"content": "toda"}, "logprobs": null, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": null, "choices": [{"delta": {"content": "y?"}, "logprobs": null, "finish_reason": null, "index": 0}], "usage": null}

data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": null, "choices": [{"delta": {}, "logprobs": null, "finish_reason": "stop", "index": 0}], "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 0, "output_tokens": 0, "input_tokens_details": null}}

data: {"id": "foaicmpl-503ab14f-3f22-46ab-9f91-3fb44773be38", "object": "chat.completion.chunk", "created": 1755839790, "model": "grok-3", "system_fingerprint": "", "choices": [], "usage": {"prompt_tokens": 8, "completion_tokens": 18, "total_tokens": 26, "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 0, "output_tokens": 0, "input_tokens_details": null}}

data: [DONE]
```

可以看到，响应里面有许多 `data` ，`data` 里面的 `choices` 即为最新的回答内容，与上文介绍的内容一致。`choices` 是新增的回答内容，您可以根据结果来对接到您的系统中。同时流式响应的结束是根据 `data` 的内容来判断的，如果内容为 `[DONE]`，则表示流式响应回答已经全部结束。返回的 `data` 结果一共有多个字段，介绍如下：

- `id`，生成此次对话任务的 ID，用于唯一标识此次对话任务。
- `model `，选择的 Grok 官网模型。
- `choices`，Grok 针对提问词给于的回答信息。

JavaScript 也是支持的，比如 Node.js 的流式调用代码如下：

```javascript
const options = {
  method: "post",
  headers: {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
  },
  body: JSON.stringify({
    "model": "grok-3",
    "messages": [{"role":"user","content":"Hello"}],
    "stream": true
  })
};

fetch("https://api.acedata.cloud/grok/chat/completions", options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));
```

Java 样例代码：

```java
JSONObject jsonObject = new JSONObject();
jsonObject.put("model", "grok-3");
jsonObject.put("messages", [{"role":"user","content":"Hello"}]);
jsonObject.put("stream", true);
MediaType mediaType = "application/json; charset=utf-8".toMediaType();
RequestBody body = jsonObject.toString().toRequestBody(mediaType);
Request request = new Request.Builder()
  .url("https://api.acedata.cloud/grok/chat/completions")
  .post(body)
  .addHeader("accept", "application/json")
  .addHeader("authorization", "Bearer {token}")
  .addHeader("content-type", "application/json")
  .build();

OkHttpClient client = new OkHttpClient();
Response response = client.newCall(request).execute();
System.out.print(response.body!!.string())
```

其他语言可以另外自行改写，原理都是一样的。

## 多轮对话

如果您想要对接多轮对话功能，需要对 `messages` 字段上传多个提问词，多个提问词的具体示例如下图所示：

<p><img src="https://cdn.acedata.cloud/t8cya8.png" width="400" class="m-auto"></p>

Python 样例调用代码：

```python
import requests

url = "https://api.acedata.cloud/grok/chat/completions"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "model": "grok-3",
    "messages": [{"role":"user","content":"Hello"},{"role":"assistant","content":"What model are you?"},{"role":"user","content":"What did I just say?"}]
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

通过上传多个提问词，就可以轻松实现多轮对话，可以得到如下回答：

```json
{
  "id": "foaicmpl-984ebc53-76b3-4d33-b0e8-0307ab4965af",
  "model": "grok-3",
  "object": "chat.completion",
  "created": 1755839996,
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "You said, \"Hello.\""
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 27,
    "completion_tokens": 6,
    "total_tokens": 33,
    "prompt_tokens_details": {
      "cached_tokens": 0,
      "text_tokens": 0,
      "audio_tokens": 0,
      "image_tokens": 0
    },
    "completion_tokens_details": {
      "text_tokens": 0,
      "audio_tokens": 0,
      "reasoning_tokens": 0
    },
    "input_tokens": 0,
    "output_tokens": 0,
    "input_tokens_details": null
  }
}
```

可以看到，`choices` 包含的信息与基本使用的内容是一致的，这个包含了 Grok 针对多个对话进行回复的具体内容，这样就可以根据多个对话内容来回答对应的问题了。

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

通过本文档，您已经了解了如何使用 OpenAI Chat Completion API 轻松实现官方 OpenAI ChatGPT 的对话功能。希望本文档能帮助您更好地对接和使用该 API。如有任何问题，请随时联系我们的技术支持团队。
