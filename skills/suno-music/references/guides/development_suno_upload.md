# Suno 上传参考音频 API 对接说明

SUNO 允许我们上传参考音频进行二次创作，本文档讲解相关 API 的对接方法。

普通上传只需要 `audio_url`，它是一个可以公开访问的音频 CDN 地址。`mode` 默认为 `standard`，因此现有调用无需修改。普通上传成功消耗 **0.06 Credits**；上传失败不扣费。

这里我们输入的 `audio_url` 是 `https://cdn.acedata.cloud/suno_demo.mp3`，是一个可以公开访问的 CDN 地址。

```bash
curl -X POST 'https://api.acedata.cloud/suno/upload' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "audio_url": "https://cdn.acedata.cloud/suno_demo.mp3"
}'
```

结果如下：

```
{
    "success": true,
    "task_id": "058f8450-3df4-4f8b-8b64-ebc2e59ed3bc",
    "data": {
        "audio_id": "00135f7d-cda1-4d70-b007-779f07143586",
        "lyric": "[Intro]\nHa-ha-ha-ha-ha-ha\n[Verse 1]\nCandy skies are dripping blue\nStuck in world of chewed up glue\nThe sun's a lollipop melting slow\nDripped in sugar on the ground below\nOh-oh\n[Chorus]\nIt's a bubblegum catastrophe\nSticky mess can't set it free\nPop it once it multiplies\nCandy chaos in disguise\nIt's a bubblegum catastrophe\nSticky mess can't set it free\nPop it once it multiplies\nCandy chaos in disguise\nHa-ha-ha-ha-ha hey\nHa-ha-ha-ha-ha hey\nHa-ha-ha-ha-ha hey\nHa-ha-ha-ha-ha hey\nCandy chaos in disguise\n[Verse 2]\nJellybean mountains crumble fast\nRainbows made of soda blast\nEvery step's a gummy bear trap\nMy sugar rush is taking a nap\nOh-oh\n[Bridge]\nChew it up (ha-ha-ha-ha)\nSpit it out (ha-ha-ha-ha)\nRound and round (ha-ha-ha-ha)\nWithout a doubt (ha-ha-ha-ha)\n[Chorus]\nIt's a bubblegum catastrophe\nSticky mess can't set it free\nPop it once it multiplies\nCandy chaos in disguise\nIt's a bubblegum catastrophe\nSticky mess can't set it free\nPop it once it multiplies\nCandy chaos in disguise\nHa-ha-ha-ha-ha hey\nHa-ha-ha-ha-ha hey\nHa-ha-ha-ha-ha hey\nHa-ha-ha-ha-ha hey\n[Outro]\nCotton candy clouds collapse\nChocolate rivers running laps\nEverywhere's a sugar flood\nMy shoes are drowning caramel\nHa-ha-ha-ha-ha hey\nHa-ha-ha-ha-ha hey\nHa-ha-ha-ha-ha hey\nHa-ha-ha-ha-ha hey\nIt's a bubblegum catastrophe\nSticky mess can't set it free\nPop it once it multiplies\nCandy chaos in disguise\nIt's a bubblegum catastrophe\nSticky mess can't set it free\nPop it once it multiplies\nCandy chaos in disguise",
        "style": "Upbeat bubblegum pop track with a high-energy electronic production style. The song features a bright, processed female vocal with a youthful and energetic tone, often layered with harmonies and occasional pitch-shifted ad-libs. The instrumentation is dominated by bouncy, staccato synthesizer chords, a driving four-on-the-floor electronic drum beat with crisp claps on the backbeat, and a prominent, melodic bassline. The tempo is approximately 128 BPM in a major key, utilizing a standard pop chord progression of I-V-vi-IV. Production elements include heavy use of sidechain compression, vocal chops, and shimmering sound effects that contribute to a sugary, hyper-pop aesthetic. The structure follows a verse-chorus-verse-chorus-bridge-chorus format with a high-energy build-up leading into the explosive, hook-driven choruses.",
        "image_url": "https://cdn.acedata.cloud/e724d7f13d.png?example=image-001",
        "image_large_url": "https://cdn.acedata.cloud/e724d7f13d.png?example=image-002",
        "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3",
        "title": "up-d6c3970d-6db1-41e3-b966-90539c93678a",
        "duration": 131.16
    }
}
```

可以看到，`data` 始终是对象，`audio_id` 是上传后的歌曲 ID。`lyric`、`style`、`duration`、标题和媒体 URL 等分析结果为可选字段，具体以返回内容为准。

有了歌曲 ID 之后，可以通过 [Suno Audios Generation API](https://platform.acedata.cloud/documents/suno-audios) 调用 `upload_extend`、`upload_cover` 或区间取样等需要 `audio_id` 的操作。若要通过 Inspo 灵感创作功能，根据 1 到 4 段完整参考音频创作新音乐，请直接调用 `action=inspo` 并传入原始公开音频 URL 列表；服务会自动完成上传和分析，无需客户端组装音频 metadata。

## 增强上传模式

> `audio_url` 是输入地址，会直接交给音频处理流程，不会由终态媒体持久化服务预先转存。请确保它在任务处理期间可公开访问。

当普通上传无法处理您拥有或已获授权使用的音频时，可以设置 `mode` 为 `enhanced`。该模式还必须提供 1 至 100 个字符的 `name`，并使用公开可访问的 HTTPS `audio_url`。

增强上传固定采用异步处理，通常需要 2 分钟或更长时间。成功处理消耗 **1.87 Credits**；处理失败不扣费。

```bash
curl -X POST 'https://api.acedata.cloud/suno/upload' \
  -H 'authorization: Bearer {token}' \
  -H 'content-type: application/json' \
  -d '{
    "audio_url": "https://cdn.acedata.cloud/suno_demo.mp3",
    "mode": "enhanced",
    "name": "My Song"
  }'
```

接口会立即返回 `task_id` 和 `trace_id`。使用 [Suno Tasks API](https://platform.acedata.cloud/documents/suno-tasks) 查询任务，成功后从 `response.data.audio_id` 读取上传后的音频 ID。也可以提供 HTTPS `callback_url` 接收终态。

增强上传得到的 `audio_id` 可用于 Cover、Samples 和 Mashup。伴奏与 MIDI 提取、全轨分离以及人声/伴奏分离仍可能受音频所属账号限制；未列出的操作不保证支持跨账号使用。音频越短，处理成功率通常越高。
