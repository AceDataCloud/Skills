# Suno 混曲歌词生成 API 对接说明

如果你想使用俩首歌曲的歌词来生成混合歌曲，可以先使用该API来生成对应的歌词，API 是 [Suno MashupLyrics Generation API](https://platform.acedata.cloud/documents/suno-mashup-lyrics)。

该 API 主要输入参数是 `lyrics_a`、`lyrics_b`，填写样例如下：

![](https://cdn.acedata.cloud/g9n3t6.png)

点击运行，结果如下：

```
{
  "success": true,
  "task_id": "80aa3cd3-ca87-4ca3-82d2-1830e3d8f53a",
  "data": {
    "text": "Sambuy come back  \nBluespawn, greenspawn are making you a spawn  \n\nSambuy come  \nSambuy come back  \nBluespawn, greenspawn are making you a spawn  \n\nSambuy come  \nSambuy come back  \nBluespawn, greenspawn are making you a spawn  \n\nSambuy come  \nSambuy come back  \nSambuy come, Sambuy come back  \nBluespawn, greenspawn are making you a spawn  \n\nSambuy come  \nSambuy come back  \nBluespawn, greenspawn are making you a spawn  \nSambuy come back",
    "title": "Lyrics Mashup",
    "tags": [],
    "status": "complete"
  }
}
```

可以看到，`data` 的 `text` 字段就是歌词信息。

有了歌词之后，我们便可以使用 [Suno Audios Generation API](https://platform.acedata.cloud/documents/suno-audios) 来进行自定义歌曲生成了。
