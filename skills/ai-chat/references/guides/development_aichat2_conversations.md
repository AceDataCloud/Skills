# AI Chat v2 API 对接说明

AI Chat v2 API（`/aichat2/conversations`）是新一代的对话接口，是 [AI Chat API](https://platform.acedata.cloud/documents/aichat-conversations) 的全面升级版本。它在 v1 简洁、托管多轮对话的基础上，扩展了：

- **多模态用户输入**：通过结构化 `message` 字段直接传文本 + 图片 + 文件块，无需先用 `references` 间接附加。
- **Agent 化工具调用**：内置一套联网搜索、网页抓取、文件读取等工具，并可挂载用户授权的 MCP 服务器（Google Drive、Notion、Slack、GitHub 等），模型可在一次请求里多轮自主调用工具完成复杂任务。
- **结构化流式事件**：通过 `accept: text/event-stream` 或 `application/x-ndjson` 可拿到逐 token 的 `text_delta`、`tool_use`、`tool_result`、`thinking`、`citation`、`card`、`artifact` 等事件，便于在前端按对应类型分别渲染。
- **可中断 / 可恢复**：模型在需要用户补充信息时会发出 `ask_user_question` 事件并暂停，下次调用通过 `tool_results` 回填答案即可继续。
- **新增 CRUD 动作**：在同一个 endpoint 上通过 `action` 字段完成 `retrieve` / `retrieve_batch` / `update` / `delete`，无需额外的会话管理 API。
- **持续更新的模型列表**：默认接入 GPT-5.4、Claude Opus 4.8、Claude Sonnet 4.6、Gemini 3.1 Pro、GLM 5.1、DeepSeek V4、Kimi K3 等当代模型。

同时它在请求体层面**完全向后兼容 v1**：只传 `model` + `question`（+ 可选 `stateful` / `id` / `references` / `preset`）即可得到与 v1 等价的 `{answer, id}` JSON 响应，所以从 `/aichat/conversations` 迁移过来不需要重写客户端，只需把路径换为 `/aichat2/conversations`。

> 如果你目前在使用 `/aichat/conversations`，旧接口仍会保留服务，可以按自己的节奏迁移。

## 申请流程

要使用 AI Chat v2 API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[AI Chat v2 API →](https://platform.acedata.cloud/documents/aichat2-conversations)

## 基本使用

最简单的用法和 v1 完全一致：传 `model` + `question`，拿到 `{answer, id}`。

CURL 示例：

```shell
curl -X POST 'https://api.acedata.cloud/aichat2/conversations' \
  -H 'accept: application/json' \
  -H 'authorization: Bearer {token}' \
  -H 'content-type: application/json' \
  -d '{
    "model": "gpt-5.4",
    "question": "用一句话介绍下 AceDataCloud。"
  }'
```

返回结果：

```json
{
  "answer": "AceDataCloud 是一个聚合主流 AI 模型与多模态服务的统一 API 平台，开发者通过一个密钥即可调用 GPT、Claude、Gemini、Midjourney、Suno、Veo 等多家服务。",
  "id": "f2f4b3e8-0c0a-4d3a-aaa2-7ff80c0a1c44"
}
```

Python 示例：

```python
import requests

url = "https://api.acedata.cloud/aichat2/conversations"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json",
}

payload = {
    "model": "gpt-5.4",
    "question": "用一句话介绍下 AceDataCloud。",
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

可用的 `model` 取值可在右侧的 Try 面板下拉里直接看到，常用类别包括：

- OpenAI：`gpt-5.4-mini`、`gpt-5.4-nano`、`gpt-5.2-pro`、`gpt-5.1-all`、`gpt-5-all`、`gpt-4.1`、`gpt-4o`、`gpt-4o-image`、`o3`、`o4-mini` 等
- Anthropic：`claude-opus-4-8`、`claude-opus-4-7`、`claude-opus-4-6`、`claude-opus-4-5-20251101`、`claude-sonnet-4-6`、`claude-sonnet-4-5-20250929`、`claude-haiku-4-5-20251001` 等
- Google：`gemini-3.1-pro-preview`、`gemini-3.1-pro-preview`、`gemini-3.1-flash-image`、`gemini-3.1-pro-preview`、`gemini-2.5-flash-lite` 等
- xAI：`grok-4` 等
- DeepSeek：`deepseek-v4-pro`、`deepseek-v4.1-flash`、`deepseek-v4-flash`、`deepseek-v3.2-exp`、`deepseek-r1-0528` 等
- Moonshot：`kimi-k3`、`kimi-k2.6`、`kimi-k2.5` 等
- Zhipu：`glm-5.3`、`glm-5.2`、`glm-5.1`、`glm-5`、`glm-5-turbo`、`glm-4.7`、`glm-4.5v` 等

具体计费规则参见服务页面的 Pricing 卡片。

## 多轮对话

和 v1 一样，传 `stateful: true` 开启会话保存，API 会返回一个 `id`；后续请求把 `id` 带回来即可继续对话，无需自己维护 messages 历史。

第一次请求：

```shell
curl -X POST 'https://api.acedata.cloud/aichat2/conversations' \
  -H 'accept: application/json' \
  -H 'authorization: Bearer {token}' \
  -H 'content-type: application/json' \
  -d '{
    "model": "gpt-5.4",
    "stateful": true,
    "question": "记住一个数字：42。"
  }'
```

返回：

```json
{
  "answer": "好的，我已经记住了 42。需要我用它做什么吗？",
  "id": "f2f4b3e8-0c0a-4d3a-aaa2-7ff80c0a1c44"
}
```

第二次请求，带上同一个 `id`：

```shell
curl -X POST 'https://api.acedata.cloud/aichat2/conversations' \
  -H 'accept: application/json' \
  -H 'authorization: Bearer {token}' \
  -H 'content-type: application/json' \
  -d '{
    "model": "gpt-5.4",
    "stateful": true,
    "id": "f2f4b3e8-0c0a-4d3a-aaa2-7ff80c0a1c44",
    "question": "我刚才让你记住的数字是多少？"
  }'
```

```json
{
  "answer": "你让我记住的数字是 42。",
  "id": "f2f4b3e8-0c0a-4d3a-aaa2-7ff80c0a1c44"
}
```

> `stateful` 默认是 `true`，省略和显式传 `true` 等价。如果你不希望服务端保存这一轮对话，可以显式设置 `stateful: false`。

## 流式响应

v2 支持两种流式格式，按照 `accept` 头选择：

| 场景 | `accept` | 数据形态 |
| :--- | :--- | :--- |
| Web 前端 / EventSource | `text/event-stream` | `data: {json}\n\n`，最后一行 `data: [DONE]\n\n` |
| 服务端 / CLI / Node 流式解析 | `application/x-ndjson` | 每行一个 JSON 对象 |
| 不需要流式 | `application/json`（默认） | 一次性返回 `{answer, id}` |

### NDJSON 示例

```python
import json
import requests

url = "https://api.acedata.cloud/aichat2/conversations"

headers = {
    "accept": "application/x-ndjson",
    "authorization": "Bearer {token}",
    "content-type": "application/json",
}

payload = {
    "model": "gpt-5.4",
    "stateful": True,
    "question": "用三句话介绍杭州。",
}

with requests.post(url, json=payload, headers=headers, stream=True) as resp:
    answer = ""
    for line in resp.iter_lines():
        if not line:
            continue
        event = json.loads(line)
        if event.get("type") == "text_delta":
            # 与 v1 兼容：增量片段同时通过 delta_answer 字段提供
            answer += event["content"]
            print(event["delta_answer"], end="", flush=True)
        elif event.get("type") == "done":
            print()
            print("usage =", event.get("usage"))
```

NDJSON 每一行都是结构化事件，最常见的是 `text_delta`：

```json
{"type":"text_delta","content":"杭","delta_answer":"杭","id":"f2f4b3e8-..."}
{"type":"text_delta","content":"州","delta_answer":"州","id":"f2f4b3e8-..."}
{"type":"text_delta","content":"是","delta_answer":"是","id":"f2f4b3e8-..."}
...
{"type":"done","conversation_id":"f2f4b3e8-...","usage":{"prompt_tokens":21,"completion_tokens":58,"total_tokens":79},"terminal_reason":"natural_stop"}
```

### SSE 示例

浏览器端使用 `EventSource` 不支持自定义请求体，建议使用 `fetch` + 手动按 `\n\n` 切片解析：

```javascript
const resp = await fetch("https://api.acedata.cloud/aichat2/conversations", {
  method: "POST",
  headers: {
    accept: "text/event-stream",
    authorization: "Bearer {token}",
    "content-type": "application/json",
  },
  body: JSON.stringify({
    model: "gpt-5.4",
    stateful: true,
    question: "用三句话介绍杭州。",
  }),
});

const reader = resp.body.getReader();
const decoder = new TextDecoder();
let buffer = "";
while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  buffer += decoder.decode(value, { stream: true });
  const blocks = buffer.split("\n\n");
  buffer = blocks.pop() ?? "";
  for (const block of blocks) {
    const dataLine = block.split("\n").find((l) => l.startsWith("data: "));
    if (!dataLine) continue;
    const payload = dataLine.slice(6);
    if (payload === "[DONE]") return;
    const event = JSON.parse(payload);
    if (event.type === "text_delta") process.stdout.write(event.content);
  }
}
```

### 流式事件类型

| `type` | 含义 |
| :--- | :--- |
| `text_delta` | 助手回答的增量文本片段。`content` 为新增内容；为兼容 v1，同一事件还携带 `delta_answer`（等于 `content`）和 `id`。 |
| `thinking` | 模型的思考过程（仅在所选模型暴露 reasoning 时出现）。 |
| `tool_use` | 模型决定调用一个工具，事件携带 `tool_id`、`tool_name`、`input`。 |
| `tool_result` | 工具执行结果，与上一条 `tool_use` 通过 `tool_id` 配对，`is_error` 标识是否失败。 |
| `card` | 工具产出的结构化卡片（如图片、链接预览），适合直接渲染。 |
| `citation` | 用于补充对应文本片段引用的来源 URL。 |
| `ask_user_question` | 模型需要用户补充信息时发出，对话进入 `awaiting_user_input` 状态，详见下文 [恢复暂停的对话](#恢复暂停的对话)。 |
| `artifact` | 模型生成的独立产物（如代码块、文档），可保存或下载。 |
| `system_message` | 系统提示信息（非用户与助手内容），仅用于 UI 提示。 |
| `compact` | 内部上下文被压缩的事件，无需特殊处理。 |
| `error` | 本轮发生错误，`message` 描述错误内容。 |
| `done` | 流式响应结束，携带 `usage`（含 `prompt_tokens` / `completion_tokens` / `total_tokens`）和 `terminal_reason`。 |

对于只关心最终答案的客户端，把所有 `text_delta` 的 `content` 拼接起来就和 `application/json` 模式下的 `answer` 等价。

## 多模态输入

如果用户输入包含图片或文件，传 `message`（数组）代替 `question`。每个数组元素是一个内容块：

```json
{
  "model": "gpt-5.4",
  "stateful": true,
  "message": [
    { "type": "text", "text": "这张图片里有几只猫？" },
    { "type": "image_url", "image_url": { "url": "https://cdn.acedata.cloud/cats.jpg" } }
  ]
}
```

支持的块类型：

- `text` — 普通文本，必填 `text` 字段。
- `image_url` — 图片，必填 `image_url.url`。
- `file_url` — 文件（PDF、CSV、TXT 等），必填 `file_url.url`。

### 与 v1 `references` 的关系

为了兼容旧客户端，v2 仍然识别 `references: ["https://...", ...]` 字段：

- URL 后缀是 `jpg / jpeg / png / gif / bmp / webp / svg / heic / heif`，自动转成 `image_url` 块；
- 其他扩展名转成 `file_url` 块；
- 如果还同时提供了 `question`，则把它作为一个 `text` 块前置。

因此只想从 v1 迁移又不想改请求体的话，把路径换成 `/aichat2/conversations` 即可，原 `references` 用法照常工作。

需要更精细控制（比如把多张图片放在文本之间、或者顺序很重要）就直接用 `message` 数组。

## 工具调用与 MCP

v2 的核心增强点是模型可以自主调用工具完成多步任务，**这是默认开启的**，不需要客户端在请求里做任何额外配置。常见场景：

- 用户问「帮我搜一下最近上海有什么新展览」→ 模型调用内置 web search → 把结果整理成回答。
- 用户问「读一下这个 PDF 然后写个摘要」→ 模型调用 file_read → 写摘要。
- 用户已在 [Connections](https://platform.acedata.cloud/connections) 里授权了 Google Drive / GitHub / Notion 等 → 模型可调用对应的 MCP 工具读写其数据。

在 NDJSON / SSE 流里，工具调用通过 `tool_use` 和 `tool_result` 两类事件呈现，例如：

```json
{"type":"tool_use","tool_id":"toolu_01ABCDEF","tool_name":"web_search","input":{"query":"上海 2026 春季展览"},"id":"f2f4b3e8-..."}
{"type":"tool_result","tool_id":"toolu_01ABCDEF","output":"...","is_error":false,"id":"f2f4b3e8-..."}
{"type":"text_delta","content":"目前","delta_answer":"目前","id":"f2f4b3e8-..."}
{"type":"text_delta","content":"上海","delta_answer":"上海","id":"f2f4b3e8-..."}
...
```

如果你不想在前端展示工具调用细节，忽略 `tool_use` / `tool_result` / `card` / `citation` 这几类事件即可，模型最终输出依然通过 `text_delta` 流出。

`max_turns` 可以限制本次请求里模型最多自我调用工具几轮，默认上限由平台决定。把它设小（比如 `max_turns: 1`）可以强制单次回答、不允许任何工具调用。

## 异步执行与无人值守授权

如果你的调用来自告警 Webhook、CI/CD、监控系统或其他后台任务，可以设置 `async: true` 让接口立即返回任务 ID，后台继续执行：

```json
{
  "model": "gpt-5.5",
  "async": true,
  "question": "我的服务报警了，用个人微信通知微信群「AceDataCloud团队」……"
}
```

返回示例：

```json
{
  "task_id": "f2f4b3e8-0c0a-4d3a-aaa2-7ff80c0a1c44",
  "conversation_id": "f2f4b3e8-0c0a-4d3a-aaa2-7ff80c0a1c44",
  "id": "f2f4b3e8-0c0a-4d3a-aaa2-7ff80c0a1c44",
  "status": "queued"
}
```

之后可用 `action: retrieve` + `id` 查询会话结果；也可以提供 `callback_url`，任务完成后平台会把 `{ status, answer, usage, error }` POST 到你的回调地址。`callback_url` 必须使用 `http` / `https`，且不能直接填写 `localhost` 或私有 IP 字面地址。

后台任务通常没有人能点击确认。如果你希望某些 Skill 或 MCP Server 在无人值守模式下执行发送、发布、写入等动作，请在请求体里显式传预授权列表：

```json
{
  "model": "gpt-5.5",
  "async": true,
  "allowed_skills": ["acedatacloud/personal-wechat"],
  "allowed_mcp_servers": [],
  "question": "我的服务报警了，用个人微信通知微信群「AceDataCloud团队」……"
}
```

`allowed_skills` 里的值是已连接 Skill 的 slug；`allowed_mcp_servers` 里的值是已连接 MCP Server 的 slug。未列入预授权的 Skill / MCP Server 在无人值守模式下仍只能预览、dry-run 或拒绝执行写操作。

如果需要更细的控制，也可以使用等价的 `unattended_policy` 对象：

```json
{
  "unattended_policy": {
    "allowed_skills": ["acedatacloud/personal-wechat"],
    "allowed_mcp_servers": [],
    "expires_at": 1790000000
  }
}
```

预授权就是这两个列表本身：列表为空即不授权任何能力，无需额外的开关字段。

注意：预授权只代表「本次请求允许这些能力在无人值守模式下跳过人工确认」。具体 Skill 仍必须支持 `--unattended-confirm` 或对应的安全机制；否则它会继续 dry-run，不会直接执行写操作。

## 恢复暂停的对话

某些工具会让模型「反问用户」，模型这时会发出一个 `ask_user_question` 事件，对话被冻结在 `awaiting_user_input` 状态：

```json
{
  "type": "ask_user_question",
  "tool_id": "toolu_01XYZW",
  "tool_name": "ask_user_question",
  "question": "你希望生成的报告是中文还是英文？",
  "options": ["中文", "英文"],
  "id": "f2f4b3e8-..."
}
```

在前端把这个事件渲染成卡片让用户选答案，然后用同一个 `id` 发起下一次请求，把答案通过 `tool_results` 回填：

```shell
curl -X POST 'https://api.acedata.cloud/aichat2/conversations' \
  -H 'accept: text/event-stream' \
  -H 'authorization: Bearer {token}' \
  -H 'content-type: application/json' \
  -d '{
    "model": "gpt-5.4",
    "stateful": true,
    "id": "f2f4b3e8-0c0a-4d3a-aaa2-7ff80c0a1c44",
    "tool_results": [
      {
        "tool_use_id": "toolu_01XYZW",
        "output": "中文"
      }
    ]
  }'
```

请求体中 `tool_use_id` **必须**和暂停时的 `tool_id` 完全一致；不一致会返回 400。当请求里同时存在 `tool_results` 时，`question` / `message` / `references` 都会被忽略。

如果用户决定放弃这个问题，直接传一个新的 `question` / `message` 即可，平台会自动把暂停的工具调用标记为「用户跳过」。

## 会话管理（CRUD）

v2 在同一个 endpoint 上通过 `action` 字段提供轻量级会话管理，无需另外开 API。

### `action: retrieve` —— 拉取一个会话

```shell
curl -X POST 'https://api.acedata.cloud/aichat2/conversations' \
  -H 'accept: application/json' \
  -H 'authorization: Bearer {token}' \
  -H 'content-type: application/json' \
  -d '{
    "action": "retrieve",
    "id": "f2f4b3e8-0c0a-4d3a-aaa2-7ff80c0a1c44"
  }'
```

返回完整的会话文档（包含 `messages` 历史、`model`、`title`、`tools_used` 等）。

### `action: retrieve_batch` —— 列出会话摘要

```json
{
  "action": "retrieve_batch",
  "model_group": "chatgpt",
  "limit": 20,
  "offset": 0
}
```

返回 `{ items: [...], total }`。**摘要不包含 `messages`**，适合做侧边栏列表；如果用户点开某条会话，再用 `action: retrieve` 单独拉取它的完整消息。

可选过滤参数：`user_id`、`application_id`、`model_group`、`model`。

### `action: update` —— 改标题或重写历史

```json
{
  "action": "update",
  "id": "f2f4b3e8-0c0a-4d3a-aaa2-7ff80c0a1c44",
  "title": "杭州旅行计划"
}
```

`messages` 也可以传，但服务端会做严格的 schema 校验（必须是折叠后的 `ToolUseContent` 形态），不符合会返回 400。一般只建议用来改 `title`。

### `action: delete` —— 删除一个会话

```json
{
  "action": "delete",
  "id": "f2f4b3e8-0c0a-4d3a-aaa2-7ff80c0a1c44"
}
```

返回 `{ id, success: true }`。删除后无法恢复，请确认后再调用。

## 从 v1 平滑迁移

如果你已经在使用 [`/aichat/conversations`](https://platform.acedata.cloud/documents/aichat-conversations)，迁移到 v2 几乎不需要改代码：

1. 把 URL 由 `https://api.acedata.cloud/aichat/conversations` 改成 `https://api.acedata.cloud/aichat2/conversations`。
2. 如果你之前传的是 v1 模型名（如 `gpt-3.5`、`gpt-4-browsing` 等），切换到 v2 时建议升级到当代模型（如 `gpt-5.4`、`claude-opus-4-8`、`gemini-3.1-pro-preview` 等）。
3. NDJSON 流的字段保持向后兼容：每个 `text_delta` 事件依然带 `delta_answer` 与 `id`，因此原来按行解析 `delta_answer` 的客户端无需改动。

迁移之后可以按需启用 v2 的新能力（多模态 `message`、SSE、工具调用、`action` CRUD），按节奏推进即可。

## 错误处理

错误响应统一为：

```json
{
  "error": {
    "code": "chat_error",
    "message": "model service returned an error"
  },
  "trace_id": "2cf86e86-22a4-46e1-ac2f-032c0f2a4e89"
}
```

常见错误：

- `400 bad_request`：缺少必填字段、`tool_use_id` 不匹配、`messages` schema 非法等。
- `401 invalid_token`：`authorization` 头不正确。
- `404 not_found`：`action: retrieve / update / delete` 时 `id` 对应的会话不存在。
- `429 too_many_requests`：触发了速率限制。
- `500 chat_error`：上游 LLM 报错或本轮 `completion_tokens=0`（按未消费处理，不会扣费）。

在流式响应里，错误以 `{"type":"error","message":"..."}` 事件发出，紧接着流就会结束。

## 结论

AI Chat v2 API 在向后兼容 v1 的同时，把对话从「单轮 / 多轮问答」升级为「Agent 化的可观测对话」：多模态输入、工具调用、可暂停 / 可恢复、流式结构化事件、内建 CRUD。建议新接入直接使用 v2；已有 v1 集成可以分阶段平滑迁移。如有任何问题，请随时联系我们的技术支持团队。
