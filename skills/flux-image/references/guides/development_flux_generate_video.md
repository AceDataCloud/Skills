# Flux Videos API 集成指南

Flux Videos API 使用 `POST /flux/videos` 完成视频生成、关键帧图生视频、视频续接和草稿增强。`action=generate`（默认），`mode` 选择生成模式；查询结果统一使用已有的 `POST /flux/tasks`。

> 当前为 Beta。文生视频、图生视频、视频续接和草稿增强已开放。HTTP 200 和任务 ID 只表示任务受理，须继续查询最终结果。

## 1. 获取 API Token

1. 在 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 注册或登录，创建应用并获取 API Token。一个通用 API Token 可调用平台服务；请确认应用具有 Flux 服务的调用权限和可用余额。
2. 在 [Flux 服务页面](https://platform.acedata.cloud/services/flux?tab=pricing) 查看套餐及各操作价格。余额不足时，在 [控制台余额页面](https://platform.acedata.cloud/console/coin) 充值。
3. 请求使用 `Authorization: Bearer <你的 Token>`。Token 应保存在服务端环境变量中，不要写入前端页面、公开仓库、截图或回调 URL。

![控制台申请 API Token](https://cdn.acedata.cloud/dvc3cg.jpg)

本文代码统一读取环境变量：

```bash
export ACEDATACLOUD_API_TOKEN='替换为你自己的 API Token'
```

| 项目 | 值 |
| --- | --- |
| API 根地址 | `https://api.acedata.cloud` |
| 提交视频任务 | `POST /flux/videos` |
| 查询已有任务 | `POST /flux/tasks` |
| 认证 | `Authorization: Bearer $ACEDATACLOUD_API_TOKEN` |
| 请求格式 | `Content-Type: application/json` |

完整字段与在线调试见 [Flux Videos API](https://platform.acedata.cloud/documents/flux-videos)，任务查询见 [Flux Tasks API](https://platform.acedata.cloud/documents/flux-tasks)。

## 2. 选择操作和输入

| action | mode | 输入 | 结果 |
| --- | --- | --- | --- |
| `generate`（省略 action 时的默认值） | `t2v` | `prompt` | 从文字生成视频 |
| `generate` | `i2v` | `prompt`、`keyframes` | 从一张或多张关键帧生成视频 |
| `generate` | `v2v` | `prompt`、`start_video` | 基于输入视频续接 |
| `generate` | `draft_enhance` | 自己已完成草稿的 `draft_task_id` | 增强该草稿 |

生成模型为 `flux-3`，`action` 为 `generate`（默认）。通过 `mode` 选择文生视频、图生视频、视频续接或草稿增强。

### 通用生成参数

| 参数 | 说明 |
| --- | --- |
| `mode` | 必填；`t2v`、`i2v`、`v2v` 或 `draft_enhance` |
| `prompt` | 普通生成必填；草稿增强不允许覆盖原始提示词 |
| `duration` | t2v/i2v 为 5–20 秒整数，v2v 为 5–15 秒整数，或 `auto`；最终输出时长可能与请求值有小幅差异 |
| `resolution` | `hd`、`fhd`、`qhd`、`uhd`；普通生成默认 `hd`，草稿增强默认 `fhd` |
| `aspect_ratio` | `auto`、`21:9`、`2:1`、`16:9`、`4:3`、`1:1`、`3:4`、`9:16`、`9:21` |
| `draft` | 是否先生成草稿；草稿仅支持 `hd` |
| `generate_audio` | 是否生成同步音频；`false` 是有效值，请保留显式布尔值 |
| `safety_tolerance` | 可选；0–4 的整数 |
| `async` | 推荐设为 `true`，立即返回平台任务 ID，再轮询结果 |
| `callback_url` | 可选；接收最终 JSON 结果的 HTTP(S) 地址；设置后也会异步受理 |

素材 URL 必须能够被服务读取。若用临时签名 URL，应为下载与处理预留足够的有效期。不要将网页地址当作图片或视频文件地址。

## 3. 文生视频：完整实测请求与结果

以下请求于 2026-10-02 调价前在生产接口执行成功。省略 `action` 验证了默认生成行为；`async=true` 避免长时间等待 HTTP 连接。

```bash
curl -X POST 'https://api.acedata.cloud/flux/videos' \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H 'Accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "flux-3",
    "mode": "t2v",
    "prompt": "A small toy sailboat floating on calm blue water in warm morning light, steady camera, no text.",
    "duration": 5,
    "resolution": "hd",
    "draft": true,
    "async": true
  }'
```

受理响应（真实任务 ID）：

```json
{
  "task_id": "4341eb66-3845-4972-bb86-712a6cfae845",
  "trace_id": "b0f851bd-0925-43ca-acc3-6f634c70d607"
}
```

保存自己响应中的 `task_id`，继续查询；不要使用文档示例的任务 ID 查询其他账户的结果。

```bash
curl -X POST 'https://api.acedata.cloud/flux/tasks' \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"action":"retrieve","id":"替换为本次返回的 task_id"}'
```

任务查询返回的 `response` 字段包含最终业务结果。以下为本次实测成功的 `response`，省略了外层任务元数据。文档中的视频 URL 已替换为长期示例 CDN 的同文件副本（SHA-256 一致），实际调用会返回本次任务自己的结果 URL：

```json
{
  "success": true,
  "task_id": "4341eb66-3845-4972-bb86-712a6cfae845",
  "trace_id": "b0f851bd-0925-43ca-acc3-6f634c70d607",
  "data": [
    {
      "id": "4341eb66-3845-4972-bb86-712a6cfae845",
      "model": "flux-3",
      "video_url": "https://cdn.acedata.cloud/assets/examples/flux/4341eb66-3845-4972-bb86-712a6cfae845-5f4391e1942c.mp4",
      "seconds": 5.041667,
      "width": 1280,
      "height": 704,
      "fps": 24,
      "draft_task_id": "4341eb66-3845-4972-bb86-712a6cfae845"
    }
  ],
  "usage": {
    "action": "generate",
    "seconds": 5.041667,
    "output_mp_seconds": 4.3326825781250005,
    "mode": "t2v",
    "resolution": "hd",
    "draft": true
  },
  "cost": {
    "amount": 2.6884689277500002,
    "currency": "credit",
    "list_amount": 2.9871876975000005
  }
}
```

[查看本次实测视频](https://cdn.acedata.cloud/assets/examples/flux/4341eb66-3845-4972-bb86-712a6cfae845-5f4391e1942c.mp4)。媒体检查确认输出为 1280×704、24 fps、5.041667 秒的 MP4，文件大小 2,607,276 字节。

| 响应字段 | 用途 |
| --- | --- |
| `success` | 最终任务是否成功；受理阶段返回 task_id 不等于 success=true |
| `task_id` | 平台任务 ID，用于轮询和业务幂等处理 |
| `trace_id` | 问题排查时提供给支持人员 |
| `data[].video_url` | 可读取的视频结果地址 |
| `data[].seconds/width/height/fps` | 服务端测量的实际输出时长、尺寸、帧率 |
| `data[].draft_task_id` | 草稿增强的输入 ID；只在返回可复用草稿时出现 |
| `usage` | 最终计费使用量；不要用请求 duration 覆盖实际 seconds |
| `cost.amount` | 此次最终扣取的 Credits；`currency=credit` 不是美元 |
| `cost.list_amount` | 应用用户消费优惠前的 Credits；适用时返回 |

这是调价前的历史实测：`list_amount=2.9871876975` Credits，账户当时享有 10% 消费优惠，实际 `amount=2.68846892775` Credits。2026-10-02 新价格已下调约 6.33%；相同 5.041667 秒草稿按当前价为 2.798125185 Credits（消费优惠前），如仍享有 10% 消费优惠则为 2.5183126665 Credits。历史任务账单不重新计算。其他账户的套餐与优惠可能不同；这不是所有用户固定的美元价格。

## 4. 图生视频：普通与带时间关键帧

以下为参数示例，需要替换素材 URL，不是该示例已经执行成功的声明。生成完成后按上面的流程查询，结果结构相同。

单张或两张图片使用普通数组：

```json
{
  "action": "generate",
  "model": "flux-3",
  "mode": "i2v",
  "prompt": "The camera slowly moves around the product in soft studio light.",
  "keyframes": ["https://example.com/first-frame.jpg"],
  "duration": 5,
  "resolution": "hd",
  "generate_audio": false,
  "async": true
}
```

指定关键帧时刻时，使用 `[秒数, 图片 URL]` 对：

```json
{
  "action": "generate",
  "model": "flux-3",
  "mode": "i2v",
  "prompt": "A smooth transition from morning light to a warm sunset.",
  "keyframes": [[0, "https://example.com/start.jpg"], [5, "https://example.com/end.jpg"]],
  "duration": 5,
  "resolution": "hd",
  "async": true
}
```

允许 1–10 张关键帧。带时间数组须按时间递增，时间为 0–20 秒，不可混用普通 URL 和带时间项。三张或更多普通关键帧必须明确指定 duration，不能用 auto。


### 图生视频实测输出
本次实测的匹配输入如下（仅以说明文字替代完整 base64，其余字段为真实请求）：

```json
{
  "async": true,
  "action": "generate",
  "model": "flux-3",
  "prompt": "The toy sailboat drifts slowly across calm water. A steady camera, gentle daylight, no people or text.",
  "duration": 5,
  "resolution": "hd",
  "generate_audio": false,
  "draft": false,
  "mode": "i2v",
  "keyframes": [
    "<下图 PNG 文件的原始 base64 字符串>"
  ]
}
```

![本次图生视频的参考关键帧](https://cdn.acedata.cloud/assets/examples/flux/b1106de8-d586-4e23-b489-381e2f86a10f-input-b0525db595d2.png)

[下载该 PNG 关键帧](https://cdn.acedata.cloud/assets/examples/flux/b1106de8-d586-4e23-b489-381e2f86a10f-input-b0525db595d2.png) 后，可用 Python 的 `base64.b64encode(image_bytes).decode("ascii")` 得到原始字符串，放入 keyframes 数组。不要将文档中的说明文字作为图片输入。


以下是 2026-10-01 生产任务的真实最终 response（非模拟响应）；仅视频 URL 换为哈希相同的长期示例副本。实测输入使用 1280×720 PNG 的原始 base64 字符串作为单张关键帧；上面的 URL 输入为独立参数示例。

```json
{
  "success": true,
  "task_id": "b1106de8-d586-4e23-b489-381e2f86a10f",
  "trace_id": "f62d5c56-cfb2-4f8f-b339-ef019d4c0d10",
  "data": [
    {
      "id": "b1106de8-d586-4e23-b489-381e2f86a10f",
      "model": "flux-3",
      "video_url": "https://cdn.acedata.cloud/assets/examples/flux/b1106de8-d586-4e23-b489-381e2f86a10f-bef14458cc9d.mp4",
      "seconds": 5.041667,
      "width": 1280,
      "height": 704,
      "fps": 24
    }
  ],
  "usage": {
    "action": "generate",
    "seconds": 5.041667,
    "output_mp_seconds": 4.3326825781250005,
    "mode": "i2v",
    "resolution": "hd",
    "draft": false
  },
  "cost": {
    "amount": 7.617328628625,
    "currency": "credit",
    "list_amount": 8.46369847625
  }
}
```

[查看实测视频](https://cdn.acedata.cloud/assets/examples/flux/b1106de8-d586-4e23-b489-381e2f86a10f-bef14458cc9d.mp4)。

## 5. 视频续接

`start_video` 传入已有视频文件地址，`mode=v2v`，时长最多 15 秒。

```json
{
  "action": "generate",
  "model": "flux-3",
  "mode": "v2v",
  "prompt": "Continue the sailboat drifting forward with the same steady camera.",
  "start_video": "https://example.com/source.mp4",
  "duration": 5,
  "resolution": "hd",
  "async": true
}
```


### 视频续接实测输出
本次完整实测输入如下；复现草稿增强时须替换为自己的草稿 ID。素材 URL 使用相同文件的长期示例副本：

```json
{
  "action": "generate",
  "model": "flux-3",
  "mode": "v2v",
  "start_video": "https://cdn.acedata.cloud/assets/examples/flux/b41293be-94c0-4dc7-9f39-ce04f0a8798d-c055a3079059.mp4",
  "prompt": "Continue the same sailboat drifting gently across calm water in the same continuous steady shot.",
  "duration": 5,
  "resolution": "hd",
  "generate_audio": false,
  "async": true
}
```


以下是 2026-10-01 生产任务的真实最终 response（非模拟响应）；仅视频 URL 换为哈希相同的长期示例副本。

```json
{
  "success": true,
  "task_id": "8af9aa42-7e4d-47a4-bd61-144d97440c91",
  "trace_id": "4fb49afc-abca-4039-bbaa-adb66e293544",
  "data": [
    {
      "id": "8af9aa42-7e4d-47a4-bd61-144d97440c91",
      "model": "flux-3",
      "video_url": "https://cdn.acedata.cloud/assets/examples/flux/8af9aa42-7e4d-47a4-bd61-144d97440c91-a512d6574811.mp4",
      "seconds": 5,
      "width": 1280,
      "height": 704,
      "fps": 24
    }
  ],
  "usage": {
    "action": "generate",
    "seconds": 5,
    "output_mp_seconds": 4.296875,
    "mode": "v2v",
    "resolution": "hd",
    "draft": false
  },
  "cost": {
    "amount": 18.219375,
    "currency": "credit",
    "list_amount": 20.24375
  }
}
```

[查看实测视频](https://cdn.acedata.cloud/assets/examples/flux/8af9aa42-7e4d-47a4-bd61-144d97440c91-a512d6574811.mp4)。

实测输入 `start_video` 为 [已完成的草稿视频](https://cdn.acedata.cloud/assets/examples/flux/b41293be-94c0-4dc7-9f39-ce04f0a8798d-c055a3079059.mp4)，其余参数为 duration=5、resolution=hd、generate_audio=false。

## 6. 先草稿、再增强

1. 用 `draft=true`、`resolution=hd` 生成草稿并等待成功。
2. 从最终 `data[0].draft_task_id` 取出平台草稿 ID。
3. 用同一归属的应用凭据提交增强请求：

```json
{
  "action": "generate",
  "model": "flux-3",
  "mode": "draft_enhance",
  "draft_task_id": "替换为自己的已完成草稿 ID",
  "resolution": "fhd",
  "async": true
}
```

草稿增强不能传入 `prompt`、`duration`、`aspect_ratio`、`version`、`generate_audio`、`draft`、`keyframes`、`start_video` 来覆盖原始内容。草稿缓存是临时资源，请及时增强；不承诺永久保存或固定保留天数。非本人/非当前应用草稿、未完成草稿和已失效缓存不能复用。草稿与增强是两次任务，成功后分别计费。


### 草稿增强实测输出
本次完整实测输入如下；复现草稿增强时须替换为自己的草稿 ID。素材 URL 使用相同文件的长期示例副本：

```json
{
  "action": "generate",
  "model": "flux-3",
  "mode": "draft_enhance",
  "draft_task_id": "b41293be-94c0-4dc7-9f39-ce04f0a8798d",
  "resolution": "hd",
  "async": true
}
```


以下是 2026-10-01 生产任务的真实最终 response（非模拟响应）；仅视频 URL 换为哈希相同的长期示例副本。

```json
{
  "success": true,
  "task_id": "1db6243b-4a05-4484-828c-25bb17de7108",
  "trace_id": "64f93fa1-8d18-4c8b-a6d2-888009eb7cfa",
  "data": [
    {
      "id": "1db6243b-4a05-4484-828c-25bb17de7108",
      "model": "flux-3",
      "video_url": "https://cdn.acedata.cloud/assets/examples/flux/1db6243b-4a05-4484-828c-25bb17de7108-058d92166607.mp4",
      "seconds": 5.041667,
      "width": 1280,
      "height": 704,
      "fps": 24
    }
  ],
  "usage": {
    "action": "generate",
    "seconds": 5.041667,
    "output_mp_seconds": 4.3326825781250005,
    "mode": "t2v",
    "resolution": "hd",
    "draft": false
  },
  "cost": {
    "amount": 7.617328628625,
    "currency": "credit",
    "list_amount": 8.46369847625
  }
}
```

[查看实测视频](https://cdn.acedata.cloud/assets/examples/flux/1db6243b-4a05-4484-828c-25bb17de7108-058d92166607.mp4)。

实测输入为自己的 draft_task_id=b41293be-94c0-4dc7-9f39-ce04f0a8798d、resolution=hd；最终 usage.mode=t2v 表示原始草稿模式。此任务与原草稿分别收费。

## 7. Python 端到端调用

安装 `requests`，设置自己的 Token，运行下面脚本即可完成“提交一次 → 轮询 → 输出视频 URL”。查询与网络重试都应使用原 task_id，避免重复提交付费任务。

```python
import os
import time
import requests

base_url = "https://api.acedata.cloud"
headers = {
    "Authorization": "Bearer " + os.environ["ACEDATACLOUD_API_TOKEN"],
    "Accept": "application/json",
}
payload = {
    "action": "generate",
    "model": "flux-3",
    "mode": "t2v",
    "prompt": "A small toy sailboat floating on calm blue water in warm morning light.",
    "duration": 5,
    "resolution": "hd",
    "draft": True,
    "async": True,
}
submitted = requests.post(base_url + "/flux/videos", json=payload, headers=headers, timeout=120)
submitted.raise_for_status()
accepted = submitted.json()
if accepted.get("error"):
    raise RuntimeError(accepted["error"])
task_id = accepted["task_id"]
print("Task ID:", task_id)  # 持久化保存，用于恢复轮询

# 30 分钟是本示例的客户端等待上限，不是服务的完成时限承诺。
deadline = time.monotonic() + 30 * 60
while time.monotonic() < deadline:
    polled = requests.post(
        base_url + "/flux/tasks",
        json={"action": "retrieve", "id": task_id},
        headers=headers,
        timeout=30,
    )
    polled.raise_for_status()
    task = polled.json()
    if task.get("error"):
        raise RuntimeError(task["error"])
    result = task.get("response") or task.get("result")
    if isinstance(result, dict) and result.get("success") is True:
        print("Video:", result["data"][0]["video_url"])
        print("Usage:", result.get("usage"))
        print("Cost:", result.get("cost"))
        break
    if isinstance(result, dict) and result.get("error"):
        raise RuntimeError(result["error"])
    time.sleep(10)
else:
    raise TimeoutError("Still processing; resume polling with task_id=" + task_id)
```

网络超时后，不要把未知状态当成失败并立即再提交。若已获得 task_id，继续查询该任务；记录 task_id 与 trace_id 便于排查。轮询接口本身不收取生成费用。

## 8. 使用回调

提交时增加 `callback_url`，任务完成后会向该地址 POST 最终 JSON 结果，成功结构与前述 response 一致，失败则包含 error。

```json
{
  "action": "generate",
  "model": "flux-3",
  "mode": "t2v",
  "prompt": "A small sailboat on calm water.",
  "duration": 5,
  "resolution": "hd",
  "draft": true,
  "callback_url": "https://your-server.example/flux-callback"
}
```

回调地址应可从公网访问。收到通知后按 task_id 幂等处理，尽快返回 2xx；业务处理可入队。本文不声明回调具有签名认证：在发放业务权益等敏感操作前，使用自己的 Token 查询同一任务来核对结果。回调未收到时也可继续轮询，不要重新生成。

## 9. 当前计费和价格表

2026-10-02 更新：本次视频接口各档单价下调约 6.33%，计量方式、套餐与消费优惠规则保持不变。前文历史实测 response 中的 cost 是任务完成时的账单，不代表当前报价。

视频生成按**实际输出秒数**计费。下面是当前未应用账户消费优惠的 Credits 单价，与 [Flux 价格页](https://platform.acedata.cloud/services/flux?tab=pricing) 的规则一致。

| 操作/模式 | 分辨率 | Credits 单价 |
| --- | --- | ---: |
| t2v / i2v 草稿 | hd | 0.555 / 秒 |
| v2v 草稿 | hd | 1.11 / 秒 |
| t2v / i2v / 对应草稿增强 | hd | 1.5725 / 秒 |
| 同上 | fhd | 2.6825 / 秒 |
| 同上 | qhd | 3.7 / 秒 |
| 同上 | uhd | 7.4 / 秒 |
| v2v / 对应草稿增强 | hd | 3.7925 / 秒 |
| 同上 | fhd | 4.9025 / 秒 |
| 同上 | qhd | 6.0125 / 秒 |
| 同上 | uhd | 8.7875 / 秒 |


换算美元：`实际费用（USD）= cost.amount（Credits）× 套餐 price / 套餐 amount`。充值档位和消费优惠会影响实际价格，Credits 不能直接当作 USD。失败任务不收取生成费用；最终金额以完成结果和控制台调用记录为准。

## 10. 常见问题与排查

| 情况 | 建议 |
| --- | --- |
| 参数错误（400） | 检查 action=generate、mode、duration、关键帧格式；不要混用不同生成模式的字段 |
| 认证错误（401） | 检查 Bearer Token、应用权限及凭据是否有效 |
| 内容审核拒绝（403） | 调整素材与提示词，不要原样反复提交 |
| 限流（429） | 降低并发，退避重试 |
| service_unavailable（503） | 当前操作不可用；已受理的异步任务可能在最终 response 中报告该错误 |
| task_id 已返回但还没有视频 | 继续查询 response，不把 HTTP 200 当作生成完成 |
| 草稿不能复用 | 确认本人/当前应用、任务已完成、原请求 draft=true，并检查临时缓存是否仍有效 |

反馈时提供 task_id、trace_id、请求时间和脱敏参数，不要发送 API Token。更多方式见 [Flux MCP 集成指南](https://platform.acedata.cloud/documents/flux-mcp)。
