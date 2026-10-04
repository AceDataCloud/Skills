# Luma 视频生成 API 对接说明

随着 AI 的应用变广，各类 AI 程序已逐渐普及。AI 已逐渐深入到人们的工作生活方方面面。而 AI 涉及的行业也越来越多，从最初的写作，到医疗教育，再到现在的视频。

Luma 是一个专业高质量的视频生成平台，用户只需上传素材，即可根据不同风格和效果自动生成高质量视频。该 AI 视频生成器由来自知名科技公司的团队成员开发，目标是无需复杂的编辑工具，让每个人都能轻松制作出色的视频。


然而 Luma 官方是并没有提供 API 的，AceDataCloud 提供了一套 Luma 的 API，模拟对接了 Suno 官方，可以方便快捷地生成想要的视频。

## 申请和使用

要使用 Luma Videos Generation API，首先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications) 获取您的 API Token，留作备用。

![](https://cdn.acedata.cloud/dvc3cg.jpg)

如果你尚未登录或注册，会自动跳转到登录页面邀请你注册和登录，完成后会自动返回当前页面。

**一个 API Token 即可调用平台所有服务，无需为每个服务单独申请。** 首次申请会赠送免费额度，可免费体验；额度不足时可在 [控制台](https://platform.acedata.cloud/console/coin) 充值通用余额。

> 📘 完整文档：[Luma Videos Generation API →](https://platform.acedata.cloud/documents/luma-videos)

## 基本使用

想要生成什么视频，可以任意输入一段文字，比如我想生成一个关于宇航员穿梭于太空和火山之间的视频，就可以输入 `Astronauts shuttle from space to volcano`，如图所示：

<p><img src="https://cdn.acedata.cloud/yub02j.png" width="500" class="m-auto"></p>

生成的代码如下：

<p><img src="https://cdn.acedata.cloud/ieq7yn.png" width="500" class="m-auto"></p>

主要请求参数：

- `prompt`：生成视频的提示词。
- `aspect_ratio`：视频宽高比，默认 16:9。
- `end_image_url`：可选，指定尾帧。
- `enhancement`：可选，清晰度增强开关。
- `loop`：是否生成循环视频，默认 false。
- `timeout`：可选，超时秒数。
- `callback_url`：异步回调地址。
- `async`：可选，设为 `true` 时接口立即返回 `task_id`，无需提供 `callback_url`，随后通过对应的任务查询接口轮询获取结果。

可以点击「Try」按钮直接测试 API，稍等 1-2 分钟，结果如下：

```json
{
  "success": true,
  "task_id": "e4018a99-1522-4f24-9330-62c2a9b50b59",
  "video_id": "155838f8-7f1e-44d8-b387-192f3b4b509d",
  "prompt": "Astronauts shuttle from space to volcano",
  "video_url": "https://cdn.acedata.cloud/assets/examples/gemini/04a043bd-6b23-4b4e-945c-ce48158c3eee-3a89912507c7.mp4",
  "video_height": 752,
  "video_width": 1360,
  "state": "completed",
  "thumbnail_url": "https://platform.cdn.acedata.cloud/luma/e4018a99-1522-4f24-9330-62c2a9b50b59.jpg",
  "thumbnail_width": 1360,
  "thumbnail_height": 752
}
```

可以看到这时候我们就得到了这个视频的相关信息，包括视频ID、视频链接、视频封面等内容。

字段说明如下：

- success：生成是否成功，如果成功则为 `true`，否则为 `false`
- task_id：此处视频生成任务的唯一ID
- video_id：此处视频生成任务产生的视频唯一ID
- prompt：此处视频生成任务的关键词
- video_url：此处视频生成任务的结果视频链接
- video_height：生成后的视频封面图片的高度
- video_width：生成后的视频封面图片的宽度
- state：此处视频生成任务的状态，如果任务完成的话则为 `completed`。
- thumbnail_url：生成后的视频封面图片的链接
- thumbnail_width：生成后的视频封面图片的宽度
- thumbnail_height：生成后的视频封面图片的高度

## 自定义首尾帧生成

如果想通过自定义视频的首尾帧来生成视频，可以输入首尾帧的图片链接：

这时候视频首帧 `start_image_url` 字段可以传入以下图片作为视频的首帧：

![首帧](https://cdn.acedata.cloud/r9vsv9.png)


接下来我们要根据首尾帧、关键词自定义生成视频，就可以指定如下内容：

- action：视频生成任务的行为，通常是普通生成 `generate` 和扩展生成 `extend`，默认为 `generate`。
- start_image_url：指定生成视频的首帧。
- end_image_url：指定生成视频的尾帧。
- prompt：生成视频的关键词内容。

填写样例如下：

<p><img src="https://cdn.acedata.cloud/zvzydx.png" width="500" class="m-auto"></p>

填写完毕之后自动生成了代码如下：

<p><img src="https://cdn.acedata.cloud/tx80pu.png" width="500" class="m-auto"></p>

对应的代码：

```python
import requests

url = "https://api.acedata.cloud/luma/videos"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "start_image_url": "https://cdn.acedata.cloud/r9vsv9.png",
    "action": "generate",
    "prompt": "Astronauts shuttle from space to volcano"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

得到的结果如下：

```json
{
  "success": true,
  "task_id": "12a18694-fd4b-47e7-9c50-34f30862cff6",
  "video_id": "0105c090-03a5-425a-8026-523341cd575b",
  "prompt": "Astronauts shuttle from space to volcano",
  "video_url": "https://platform.cdn.acedata.cloud/luma/12a18694-fd4b-47e7-9c50-34f30862cff6.mp4",
  "video_height": 656,
  "video_width": 1552,
  "state": "completed",
  "thumbnail_url": "https://platform.cdn.acedata.cloud/luma/12a18694-fd4b-47e7-9c50-34f30862cff6.jpg",
  "thumbnail_width": 1552,
  "thumbnail_height": 656
}
```

最后得到的结果与上文的类似的，生成的视频首帧包含了我们传入的图片，当然也可以同时传入首尾帧图片链接来生成视频，只需要在上面的基础上再加一个尾帧图片即可，尾帧的图片信息如下：

![尾帧](https://cdn.acedata.cloud/0iad3k.png)

填写样例如下：

<p><img src="https://cdn.acedata.cloud/20igwi.png" width="500" class="m-auto"></p>

最后得出如下结果：

```json
{
  "success": true,
  "task_id": "d1cb723a-e554-4775-94a4-bb6ae8c7ea67",
  "video_id": "6bebd0d2-f793-472e-9326-38528a9273bb",
  "prompt": "Astronauts shuttle from space to volcano",
  "video_url": "https://platform.cdn.acedata.cloud/luma/d1cb723a-e554-4775-94a4-bb6ae8c7ea67.mp4",
  "video_height": 656,
  "video_width": 1552,
  "state": "completed",
  "thumbnail_url": "https://platform.cdn.acedata.cloud/luma/d1cb723a-e554-4775-94a4-bb6ae8c7ea67.jpg",
  "thumbnail_width": 1552,
  "thumbnail_height": 656
}
```

结果与上文是类似的，生成的视频同时包含了首帧与尾帧的图片，这也就完成了自定义首尾帧来生成视频。


## 视频扩展功能

如果想对生成的视频进行继续生成的话，可以将参数 `action` 设置为 `extend` ，并且输入需要继续生成视频的ID或者视频链接，视频ID和视频链接的获取是根据基本使用来获取，如下图所示：

<p><img src="https://cdn.acedata.cloud/fwknj4.png" width="500" class="m-auto"></p>

这时候可以看到视频的ID为：

```
"video_id": "0105c090-03a5-425a-8026-523341cd575b",
"video_url": "https://platform.cdn.acedata.cloud/luma/12a18694-fd4b-47e7-9c50-34f30862cff6.mp4"
```

> 注意，这里的视频中 `video_id` 和 `video_url` 是生成后视频的ID和视频链接，如果你不知道如何生成视频，可以参考上文的基本使用来生成视频。

要想继续生成视频的话必须上传视频链接或视频的ID，下面演示使用视频ID来进行扩展，接下来我们要必须填关键词自定义生成视频，就可以指定如下内容：

- action：此时扩展视频的行为，在这应为 `extend` 。
- prompt：需要扩展视频的关键词。
- video_url：需要扩展生成视频的链接。
- video_id：需要扩展生成视频的唯一ID。
- end_image_url：扩展生成视频可指定尾帧的图片链接，可选参数。

填写样例如下：

<p><img src="https://cdn.acedata.cloud/vv0rxk.png" width="500" class="m-auto"></p>

填写完毕之后自动生成了代码如下：

<p><img src="https://cdn.acedata.cloud/woapxi.png" width="500" class="m-auto"></p>

对应的Python代码：

```python
import requests

url = "https://api.acedata.cloud/luma/videos"

headers = {
    "accept": "application/json",
    "authorization": "Bearer {token}",
    "content-type": "application/json"
}

payload = {
    "action": "extend",
    "video_id": "0105c090-03a5-425a-8026-523341cd575b",
    "prompt": "Astronauts shuttle from space to volcano"
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)
```

点击运行，可以发现会得到一个结果，如下：

```json
{
  "success": true,
  "task_id": "c6e529d1-a06d-4c12-91b2-c855135131c3",
  "video_id": "36908c49-c2bb-4a11-bd5a-b8512b004818",
  "prompt": "Astronauts shuttle from space to volcano",
  "video_url": "https://platform.cdn.acedata.cloud/luma/c6e529d1-a06d-4c12-91b2-c855135131c3.mp4",
  "video_height": 656,
  "video_width": 1552,
  "state": "completed",
  "thumbnail_url": "https://platform.cdn.acedata.cloud/luma/c6e529d1-a06d-4c12-91b2-c855135131c3.jpg",
  "thumbnail_width": 1552,
  "thumbnail_height": 656
}
```

可以看出该视频是在需要扩展的视频基础上进行扩展的，结果内容与上文的是一致的，这也就实现歌曲的继续生成功能。

当然我们也可以指定视频的链接来进行扩展生成，填如下信息：

<p><img src="https://cdn.acedata.cloud/0cv0hg.png" width="500" class="m-auto"></p>

运行后得到了如下结果：

```json
{
  "success": true,
  "task_id": "1dcb5902-a7be-4b77-ba5d-dd8ec82b26ca",
  "video_id": "f0187dc2-339f-4a08-a435-c3a3341f620a",
  "prompt": "Astronauts shuttle from space to volcano",
  "video_url": "https://platform.cdn.acedata.cloud/luma/1dcb5902-a7be-4b77-ba5d-dd8ec82b26ca.mp4",
  "video_height": 656,
  "video_width": 1552,
  "state": "completed",
  "thumbnail_url": "https://platform.cdn.acedata.cloud/luma/1dcb5902-a7be-4b77-ba5d-dd8ec82b26ca.jpg",
  "thumbnail_width": 1552,
  "thumbnail_height": 656
}
```

根据结果可以看出根据视频链接也可以实现视频扩展的功能。

最后我们还可以对扩展视频中指定一个尾帧图片来进行扩展，下面是尾帧图片信息：

![尾帧](https://cdn.acedata.cloud/0iad3k.png)

接下来在上面的基础上添加尾帧图片信息，具体的如下所示：

<p><img src="https://cdn.acedata.cloud/9p1vrj.png" width="500" class="m-auto"></p>

点击运行后得到如下信息：

```json
{
  "success": true,
  "task_id": "b816b2b4-c345-4673-9e19-83e91f91b643",
  "video_id": "c5400053-63e6-4206-8082-31cf9dd1e7ed",
  "prompt": "Astronauts shuttle from space to volcano",
  "video_url": "https://platform.cdn.acedata.cloud/luma/b816b2b4-c345-4673-9e19-83e91f91b643.mp4",
  "video_height": 656,
  "video_width": 1552,
  "state": "completed",
  "thumbnail_url": "https://platform.cdn.acedata.cloud/luma/b816b2b4-c345-4673-9e19-83e91f91b643.jpg",
  "thumbnail_width": 1552,
  "thumbnail_height": 656
}
```

可以看出，在上文扩展视频的基础上，还可以指定尾帧图片来进行扩展。


## 异步回调

由于 Luma 生成视频的时间相对较长，大约需要 1-2 分钟，如果 API 长时间无响应，HTTP 请求会一直保持连接，导致额外的系统资源消耗，所以本 API 也提供了异步回调的支持。

整体流程是：客户端发起请求的时候，额外指定一个 `callback_url` 字段，客户端发起 API 请求之后，API 会立马返回一个结果，包含一个 `task_id` 的字段信息，代表当前的任务 ID。当任务完成之后，生成音乐的结果会通过 POST JSON 的形式发送到客户端指定的 `callback_url`，其中也包括了 `task_id` 字段，这样任务结果就可以通过 ID 关联起来了。

下面我们通过示例来了解下具体怎样操作。

首先，Webhook 回调是一个可以接收 HTTP 请求的服务，开发者应该替换为自己搭建的 HTTP 服务器的 URL。此处为了方便演示，使用一个公开的 Webhook 样例网站 https://webhook.site/，打开该网站即可得到一个 Webhook URL，如图所示：

<p><img src="https://cdn.acedata.cloud/q78okf.png" width="500" class="m-auto"></p>

将此 URL 复制下来，就可以作为 Webhook 来使用，此处的样例为 https://webhook.site/0c87ca0e-cd74-4577-8d68-f2b80fbf8a13。

接下来，我们可以设置字段 `callback_url` 为上述 Webhook URL，同时填入 `prompt`，如图所示：

<p><img src="https://cdn.acedata.cloud/n2fjvi.png" width="500" class="m-auto"></p>

点击运行，可以发现会立即得到一个结果，如下：

```json
{
  "task_id": "732f8282-7cf8-401c-95f2-42c33aa079a6"
}
```

稍等片刻，我们可以在 https://webhook.site/0c87ca0e-cd74-4577-8d68-f2b80fbf8a13 上观察到生成歌曲的结果，如图所示：

![](https://cdn.acedata.cloud/1hwm5m.png)

内容如下：

```json
{
    "success": true,
    "task_id": "732f8282-7cf8-401c-95f2-42c33aa079a6",
    "video_id": "4d8013c3-5de0-41aa-966e-0b1a51d1c633",
    "prompt": "Astronauts shuttle from space to volcano",
    "video_url": "https://platform.cdn.acedata.cloud/luma/732f8282-7cf8-401c-95f2-42c33aa079a6.mp4",
    "video_height": 752,
    "video_width": 1360,
    "state": "completed",
    "thumbnail_url": "https://platform.cdn.acedata.cloud/luma/732f8282-7cf8-401c-95f2-42c33aa079a6.jpg",
    "thumbnail_width": 1360,
    "thumbnail_height": 752
}
```

可以看到结果中有一个 `task_id` 字段，其他的字段都和上文类似，通过该字段即可实现任务的关联。
