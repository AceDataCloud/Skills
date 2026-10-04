# OpenAI Embeddings API 申请及使用

OpenAI 词向量服务，用于生成表示输入文本的词向量结果。

本文档主要介绍 OpenAI Embeddings API 操作的使用流程，利用它我们可以创建表示输入文本的嵌入向量。。

## 申请流程

要使用 OpenAI Embeddings API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[OpenAI Embeddings API →](https://platform.acedata.cloud/documents/openai-embeddings)

## 基本使用

接下来就可以在界面上填写对应的内容，如图所示：

<p><img src="https://cdn.acedata.cloud/4qtbvr.png" width="500" class="m-auto"></p>

在第一次使用该接口时，我们至少需要填写三个内容，一个是 `authorization`，直接在下拉列表里面选择即可。另一个参数是 `model`， `model` 就是我们选择使用 OpenAI 官网模型类别，这里我们主要有 3 种模型，详情可以看我们提供的模型。最后一个参数是`input`，`input` 是我们需要转换的词向量文本。

同时您可以注意到右侧有对应的调用代码生成，您可以复制代码直接运行，也可以直接点击「Try」按钮进行测试。

可选参数：

- `dimensions`：裁剪向量维度，默认输出完整维度。
- `encoding_format`：返回格式，可选 `float` 或 `base64`。

<p><img src="https://cdn.acedata.cloud/gqulm9.png" width="500" class="m-auto"></p>

Python 样例调用代码：

```python
import requests

url = "https://api.acedata.cloud/openai/embeddings"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "input": "The food was delicious and the waiter...",
    "model": "text-embedding-ada-002",
    "encoding_format": "float"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

调用之后，我们发现返回结果如下：

```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "index": 0,
      "embedding": [
        0.0022756963,
        -0.009305916,
        0.015742613,
        -0.0077253063,
        -0.0047450014,
        0.014917395,
        -0.009807394,
        -0.038264707,
        -0.0069127847,
        -0.028590616,
        0.025251659,
        ....
        -0.014079482,
        -0.015425222,
        0.0040753055,
        0.002727979,
        -0.03138366,
        0.041159317,
        -0.017608874,
        -0.018637223,
        0.014587308,
        0.010486611,
        -0.015387135,
        -0.019424353,
        -0.002800979
      ]
    }
  ],
  "model": "text-embedding-ada-002",
  "usage": {
    "prompt_tokens": 8,
    "total_tokens": 8
  }
}
```

返回结果一共有多个字段，介绍如下：

- `model`，此次文本转词向量所采用的模型。
- `usage`，此次文本转词向量所使用的token信息。
- `data`，文本转化后的词向量结果。

其中 `data` 是包含了文本对应的词向量的具体信息，它里面的 `embedding` 是生成的词向量具体结果。


## 错误处理

在调用 API 时，如果遇到错误，API 会返回相应的错误代码和信息。例如：

- `400 token_mismatched`：Bad request, possibly due to missing or invalid parameters.
- `400 api_not_implemented`：Bad request, possibly due to missing or invalid parameters.
- `401 invalid_token`：Unauthorized, invalid or missing authorization token.
- `429 too_many_requests`：Too many requests, you have exceeded the rate limit.
- `500 api_error`：Internal server error, something went wrong on the server.

### 错误响应示例

```json
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

通过本文档，您已经了解了如何使用 OpenAI Embeddings API 轻松使用官方 OpenAI 的词向量生成的功能。希望本文档能帮助您更好地对接和使用该 API。如有任何问题，请随时联系我们的技术支持团队。
