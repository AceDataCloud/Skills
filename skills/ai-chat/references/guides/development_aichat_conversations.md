# AI Chat API 对接说明

我们知道，市面上一些问答 API 的对接还是相对没那么容易的，比如说 OpenAI 的 Chat Completions API，它有一个 `messages` 字段，如果要完成连续对话，需要我们把所有的上下文历史全部传递，同时还需要处理 Token 超出限制的问题。

AceDataCloud 提供的 AI 问答 API 针对上述情况进行了优化，在保证问答效果不变的情况下，对连续对话的实现进行了封装，对接时无需再关心 messages 的传递，也无需关心 Token 超出限制的问题（API 内部自动进行了处理），同时也提供了对话查询、修改等功能，使得整体的对接大大简化。

本文档会介绍下 AI 问答 API 的对接说明。

## 申请流程

要使用 AI 问答 API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[AI 问答 API →](https://platform.acedata.cloud/documents/aichat-conversations)

## 基本使用

首先先了解下基本的使用方式，就是输入问题，获得回答，只需要简单地传递一个 `question` 字段，并指定相应模型即可。

比如说询问：“What's your name？”，我们接下来就可以在界面上填写对应的内容，如图所示：

![](https://cdn.acedata.cloud/xqxda4.png)

可以看到这里我们设置了 Request Headers，包括：

- `accept`：想要接收怎样格式的响应结果，这里填写为 `application/json`，即 JSON 格式。
- `authorization`：调用 API 的密钥，申请之后可以直接下拉选择。

另外设置了 Request Body，包括：

- `model`：模型的选择，比如主流的 GPT 3.5，GPT 4 等。
- `question`：需要询问的问题，可以是任意的纯文本。

选择之后，可以发现右侧也生成了对应代码，如图所示：

<p><img src="https://cdn.acedata.cloud/dvkps6.png" width="500" class="m-auto"></p>

点击「Try」按钮即可进行测试，如上图所示，这里我们就得到了如下结果：

```json
{
  "answer": "I am an AI language model developed by OpenAI and I don't have a personal name. However, you can call me GPT or simply Chatbot. How can I assist you today?"
}
```

可以看到，这里返回的结果中有一个 `answer` 字段，就是该问题的回答。我们可以输入任意问题，就可以得到任意的回答。

如果你不需要任何多轮对话的支持，这个 API 可以极大方便你的对接。

另外如果想生成对应的对接代码，可以直接复制生成，例如 CURL 的代码如下：

```shell
curl -X POST 'https://api.acedata.cloud/aichat/conversations' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "model": "gpt-3.5",
  "question": "What's your name?"
}'
```

Python 的对接代码如下：

```python
import requests

url = "https://api.acedata.cloud/aichat/conversations"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "model": "gpt-3.5",
    "question": "What's your name?"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

## 多轮对话

如果您想要对接多轮对话功能，需要传递一个额外参数 `stateful`，其值为 `true`，后续的每次请求都要携带该参数。传递了 `stateful` 参数之后，API 会额外返回一个 `id` 参数，代表当前对话的 ID，后续我们只需要将该 ID 作为参数传递，就可以轻松实现多轮对话。

下面我们来演示下具体的操作。

第一次请求，将 `stateful` 参数设置为 `true`，并正常传递 `model` 和 `question` 参数，如图所示：

![](https://cdn.acedata.cloud/fn4bi9.png)

对应代码如下：

```shell
curl -X POST 'https://api.acedata.cloud/aichat/conversations' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "model": "gpt-3.5",
  "question": "What's your name?",
  "stateful": true
}'
```

可以得到如下回答：

```json
{
  "answer": "I am an AI language model created by OpenAI and I don't have a personal name. You can simply call me OpenAI or ChatGPT. How can I assist you today?",
  "id": "7cdb293b-2267-4979-a1ec-48d9ad149916"
}
```

第二次请求，将第一次请求返回的 `id` 字段作为参数传递，同时 `stateful` 参数依然设置为 `true`，询问「What I asked you just now?」，如图所示：

![](https://cdn.acedata.cloud/46a6kd.png)

对应代码如下：

```shell
curl -X POST 'https://api.acedata.cloud/aichat/conversations' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "model": "gpt-3.5",
  "stateful": true,
  "id": "7cdb293b-2267-4979-a1ec-48d9ad149916",
  "question": "What I asked you just now?"
}'
```

结果如下：

```json
{
  "answer": "You asked me what my name is. As an AI language model, I do not possess a personal identity, so I don't have a specific name. However, you can refer to me as OpenAI or ChatGPT, the names used for this AI model. Is there anything else I can help you with?",
  "id": "7cdb293b-2267-4979-a1ec-48d9ad149916"
}
```

可以看到，就可以根据上下文回答对应的问题了。

## 流式响应

该接口也支持流式响应，这对网页对接十分有用，可以让网页实现逐字显示效果。

如果想流式返回响应，可以更改请求头里面的 `accept` 参数，修改为 `application/x-ndjson`。

修改如图所示，不过调用代码需要有对应的更改才能支持流式响应。

![](https://cdn.acedata.cloud/axt1aa.png)

将 `accept` 修改为 `application/x-ndjson` 之后，API 将逐行返回对应的 JSON 数据，在代码层面我们需要做相应的修改来获得逐行的结果。

Python 样例调用代码：

```python
import requests

url = "https://api.acedata.cloud/aichat/conversations"

headers = {
    "accept": "application/x-ndjson",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "model": "gpt-3.5",
    "stateful": True,
    "id": "7cdb293b-2267-4979-a1ec-48d9ad149916",
    "question": "Hello"
}

response = requests.post(url, json=payload, headers=headers, stream=True)
for line in response.iter_lines():
    print(line.decode())
```

输出效果如下：

```json
{"answer": "Hello", "delta_answer": "Hello", "id": "7cdb293b-2267-4979-a1ec-48d9ad149916"}
{"answer": "Hello!", "delta_answer": "!", "id": "7cdb293b-2267-4979-a1ec-48d9ad149916"}
{"answer": "Hello! How", "delta_answer": " How", "id": "7cdb293b-2267-4979-a1ec-48d9ad149916"}
{"answer": "Hello! How can", "delta_answer": " can", "id": "7cdb293b-2267-4979-a1ec-48d9ad149916"}
{"answer": "Hello! How can I", "delta_answer": " I", "id": "7cdb293b-2267-4979-a1ec-48d9ad149916"}
{"answer": "Hello! How can I assist", "delta_answer": " assist", "id": "7cdb293b-2267-4979-a1ec-48d9ad149916"}
{"answer": "Hello! How can I assist you", "delta_answer": " you", "id": "7cdb293b-2267-4979-a1ec-48d9ad149916"}
{"answer": "Hello! How can I assist you today", "delta_answer": " today", "id": "7cdb293b-2267-4979-a1ec-48d9ad149916"}
{"answer": "Hello! How can I assist you today?", "delta_answer": "?", "id": "7cdb293b-2267-4979-a1ec-48d9ad149916"}
```

可以看到，响应里面的 `answer` 即为最新的回答内容，`delta_answer` 则是新增的回答内容，您可以根据结果来对接到您的系统中。

JavaScript 也是支持的，比如 Node.js 的流式调用代码如下：

```javascript
const axios = require("axios");

const url = "https://api.acedata.cloud/aichat/conversations";
const headers = {
  "Content-Type": "application/json",
  Accept: "application/x-ndjson",
  Authorization: "Bearer {token}",
};
const body = {
  question: "Hello",
  model: "gpt-3.5",
  stateful: true,
};

axios
  .post(url, body, { headers: headers, responseType: "stream" })
  .then((response) => {
    console.log(response.status);
    response.data.on("data", (chunk) => {
      console.log(chunk.toString());
    });
  })
  .catch((error) => {
    console.error(error);
  });
```

Java 样例代码：

```java
String url = "https://api.acedata.cloud/aichat/conversations";
OkHttpClient client = new OkHttpClient();
MediaType mediaType = MediaType.parse("application/json");
RequestBody body = RequestBody.create(mediaType, "{\"question\": \"Hello\", \"stateful\": true, \"model\": \"gpt-3.5\"}");
Request request = new Request.Builder()
        .url(url)
        .post(body)
        .addHeader("Content-Type", "application/json")
        .addHeader("Accept", "application/x-ndjson")
        .addHeader("Authorization", "Bearer {token}")
        .build();

client.newCall(request).enqueue(new Callback() {
    @Override
    public void onFailure(Call call, IOException e) {
        e.printStackTrace();
    }

    @Override
    public void onResponse(Call call, Response response) throws IOException {
        if (!response.isSuccessful()) throw new IOException("Unexpected code " + response);
        try (BufferedReader br = new BufferedReader(
                new InputStreamReader(response.body().byteStream(), "UTF-8"))) {
            String responseLine;
            while ((responseLine = br.readLine()) != null) {
                System.out.println(responseLine);
            }
        }
    }
});
```

其他语言可以另外自行改写，原理都是一样的。

## 模型预设

我们知道，OpenAI 相关的 API 有对应的 `system_prompt` 的概念，就是给整个模型设置一个预设，比如它叫什么名字等等。本 AI 问答 API 也暴露了这个参数，叫做 `preset`，利用它我们可以给模型增加预设，我们用一个例子来体验下：

这里我们额外添加 `preset` 字段，内容为 `You are a professional artist`，如图所示：

![](https://cdn.acedata.cloud/ird6i9.png)

对应代码如下：

```shell
curl -X POST 'https://api.acedata.cloud/aichat/conversations' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "model": "gpt-3.5",
  "stateful": true,
  "question": "What can you help me?",
  "preset": "You are a professional artist"
}'
```

运行结果如下：

```python
{
    "answer": "As a professional artist, I can offer a range of services and assistance depending on your specific needs. Here are a few ways I can help you:\n\n1. Custom Artwork: If you have a specific vision or idea, I can create custom artwork for you. This can include paintings, drawings, digital art, or any other medium you prefer.\n\n2. Commissioned Pieces: If you have a specific subject or concept in mind, I can create commissioned art pieces tailored to your preferences. This could be for personal enjoyment or as a unique gift for someone special.\n\n3. Art Consultation: If you need guidance on art selection, interior design, or how to showcase and display art in your space, I can provide professional advice to help enhance your aesthetic sense and create a cohesive look."
}
```

可以看到这里我们告诉 GPT 他是一个机器人，然后问它可以为我们做什么，他就可以扮演一个机器人的角色来回答问题了。

## 图片识别

本 AI 也能支持添加附件进行图片识别，通过 `references` 传递对应图片链接即可，比如我这里有一张苹果的图片，如图所示：

![](https://cdn.acedata.cloud/ht05g0.png)

该图片的链接是 [https://cdn.acedata.cloud/ht05g0.png](https://cdn.acedata.cloud/ht05g0.png)，我们直接将其作为 `references` 参数传递即可，同时需要注意的是，模型必须要选择支持视觉识别的模型，目前支持的是 `gpt-4-vision`，所以输入如下：

![](https://cdn.acedata.cloud/cstrbq.png)

对应的代码如下：

```shell
curl -X POST 'https://api.acedata.cloud/aichat/conversations' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "model": "gpt-4-vision",
  "question": "How many apples in the picture?",
  "references": ["https://cdn.acedata.cloud/ht05g0.png"]
}'
```

运行结果如下：

```json
{
  "answer": "There are 5 apples in the picture."
}
```

可以看到，我们就成功得到了对应图片的回答结果。

## 联网问答

本 API 还支持联网模型，包括 GPT-3.5、GPT-4 均能支持，在 API 背后有一个自动搜索互联网并总结的过程，我们可以选择模型为 `gpt-3.5-browsing` 来体验下，如图所示：

![](https://cdn.acedata.cloud/x5i8np.png)

代码如下：

```shell
curl -X POST 'https://api.acedata.cloud/aichat/conversations' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "model": "gpt-3.5-browsing",
  "question": "What's the weather of New York today?"
}'
```

运行结果如下：

```json
{
  "answer": "The weather in New York today is as follows:\n- Current Temperature: 16°C (60°F)\n- High: 16°C (60°F)\n- Low: 10°C (50°F)\n- Humidity: 47%\n- UV Index: 6 of 11\n- Sunrise: 5:42 am\n- Sunset: 8:02 pm\n\nIt's overcast with a chance of occasional showers overnight, and the chance of rain is 50%.\nFor more details, you can visit [The Weather Channel](https://weather.com/weather/tenday/l/96f2f84af9a5f5d452eb0574d4e4d8a840c71b05e22264ebdc0056433a642c84).\n\nIs there anything else you'd like to know?"
}
```

可以看到，这里它自动联网搜索了 The Weather Channel 网站，并获得了里面的信息，然后进一步返回了实时结果。

> 如果对模型回答质量有更高要求，可以将模型更换为 `gpt-4-browsing`，回答效果会更好。
