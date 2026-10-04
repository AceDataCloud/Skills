# Suno 歌词生成 API 对接说明

如果你想自定义生成歌曲，但又不太想自己编写歌词，可以使用 AceDataCloud 提供的歌词生成 API 来通过 prompt 生成歌词，API 是 [Suno Lyrics Generation API](https://platform.acedata.cloud/documents/suno-lyrics)。

该 API 主要输入参数是 `prompt`，可选 `model`（可选值 `default`、`remi-v1`，默认 `default`），填写样例如下：

![](https://cdn.acedata.cloud/p53wtj.png)

这里我们输入的 `prompt` 是 `A song about winter`，生成和冬天相关的歌曲。

点击运行，结果如下：

```json
{
  "success": true,
  "task_id": "2e26f7ff-0b82-4a60-bb9b-78db89f98b51",
  "data": [
    {
      "text": "[Verse]\nSnowflakes falling from the sky\nWinter's cold touch\nOh how it gets me high\nI bundle up in layers\nOh so cozy\nStepping out and feeling the frost on my nose\n\n[Chorus]\nOh\nWinter's cold touch\nIt's a season that I love so much\nSnowfall brings a feeling so divine\nWinter's cold touch\nIt's a magical time",
      "title": "Winter's Cold Touch",
      "status": "complete",
      "tags": ["dreamy, mellow, ballad"]
    },
    {
      "text": "[Verse]\nThe world is covered in a blanket of white\nIcicles hanging\nShimmering so bright\nThe chilly air fills my lungs with every breath\nWalking in the snow\nLeaving footprints behind\n\n[Chorus]\nWinter wonderland\nEverything is so bright\nWinter wonderland\nHold me through the night",
      "title": "Winter Wonderland",
      "status": "complete",
      "tags": ["dream pop, mellow, shoegaze"]
    }
  ],
  "started_at": 1780684179.15,
  "finished_at": 1780684186.583,
  "elapsed": 7.433
}
```

可以看到，`data` 是一个数组，每次会返回多个歌词候选，其中每个元素的 `text` 字段就是歌词内容，`title` 是标题，`tags` 是推荐的曲风标签。

有了歌词之后，我们便可以使用 [Suno Audios Generation API](https://platform.acedata.cloud/documents/suno-audios) 来进行自定义歌曲生成了。
