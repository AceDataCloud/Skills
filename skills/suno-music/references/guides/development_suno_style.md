# Suno Style API 对接说明

SUNO 允许我们输入提示词来生成增强歌曲的风格。本文档讲解相关 API 的对接方法。

该 API 只有一个输入参数，就是 `prompt`，它是需要优化的风格提示词。

这里我们输入的 `prompt` 是 `A song for Christmas`。

```python
import requests

url = "https://api.acedata.cloud/suno/style"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "prompt": "A song for Christmas"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

结果如下：

```json
{
  "success": true,
  "task_id": "8e887548-7185-48a9-b7cb-e51754f7b87b",
  "trace_id": "ac4ec363-4245-400b-9643-0b6fed8c6b20",
  "data": {
    "upsampled_tags": "Bright, festive bells and crisp acoustic guitar open, with sleigh bells and warm upright piano filling the verse. Lush strings sweep in for the pre-chorus, leading to a soaring full-band chorus enhanced by brass accents. The bridge softens with glockenspiel, then returns to a jubilant finale."
  }
}
```


可以看到，`data` 的 `upsampled_tags` 字段就是根据提示词优化后的风格参数。
