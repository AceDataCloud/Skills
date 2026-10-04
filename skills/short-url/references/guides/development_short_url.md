# Short URL API 对接说明

本文将介绍一种 Short URL API 对接说明 对接说明，它可将较长的URL转换为短的URL。

## 申请流程

要使用 Short URL API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Short URL API →](https://platform.acedata.cloud/documents/shorturl)

## 基本使用

首先先了解下基本的使用方式，就是输入需要转换的较长URL，便可获得处理后的结果，首先需要简单地传递一个 `content` 字段。我们接下来就可以在界面上填写对应的内容，如图所示：

<p><img src="https://cdn.acedata.cloud/4ascb2.png" width="500" class="m-auto"></p>

可以看到这里我们设置了 Request Headers，包括：

- `accept`：想要接收怎样格式的响应结果，这里填写为 `application/json`，即 JSON 格式。
- `authorization`：调用 API 的密钥，申请之后可以直接下拉选择。

另外设置了 Request Body，包括：

- `content`：要缩短的URL的内容。

选择之后，可以发现右侧也生成了对应代码，如图所示：

<p><img src="https://cdn.acedata.cloud/r3uakb.png" width="500" class="m-auto"></p>

点击「Try」按钮即可进行测试，如上图所示，这里我们就得到了如下结果：

```json
{
  "success": true,
  "data": {
    "url": "https://surl.id/1uHCs01xa5"
  }
}
```

返回结果一共有多个字段，介绍如下：

- `success`，此处任务是否成功的状态。
- `data`，包含了此处转换后的URL。

可以看出
原先较长的URL `https://platform.acedata.cloud/documents/shorturl` 已经成功转换为短的URL `https://surl.id/1uHCs01xa5`。

另外如果想生成对应的对接代码，可以直接复制生成，例如 CURL 的代码如下：

```shell
curl -X POST 'https://api.acedata.cloud/shorturl' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "content": "https://platform.acedata.cloud/documents/shorturl"
}'
```

Python 的对接代码如下：

```python
import requests

url = "https://api.acedata.cloud/shorturl"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "content": "https://platform.acedata.cloud/documents/shorturl"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

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

通过本文档，您已经了解了如何使用 Short URL API 将较长的URL转换为短的URL。希望本文档能帮助您更好地对接和使用该 API。如有任何问题，请随时联系我们的技术支持团队。
