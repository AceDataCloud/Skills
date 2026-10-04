# Producer 上传参考音频 API 对接说明

Producer 允许我们上传参考音频进行二次创作，本文档讲解相关 API 的对接方法。

该 API 只有一个输入参数，就是 `audio_url`，它是一个可以公开访问的 CDN 地址，支持 mp3 后缀。

这里我们输入的 `audio_url` 是 `https://cdn.acedata.cloud/suno_demo.mp3`，是一个可以公开访问的 CDN 地址。

```bash
curl -X POST 'https://api.acedata.cloud/producer/upload' \
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
  "task_id": "23e7d4ec-d1a8-429f-87d8-9f53fc3b6666",
  "data": {
    "audio_id": "d906da31-87cb-42f5-98df-2fc4969923b1",
    "lyric": "[Mandopop, Acoustic Pop]\n[Soft female vocals, bright and cheerful]\n\n[Verse 1]\n阳光洒在海边\n浪花笑得灿烂\n你和我在沙滩\n钟表停止转\n冰淇淋在融化\n手牵手去散步\n风儿轻轻吹过\n心跳不停跳\n\n[Chorus]\n夏天夏天\n时间停在这一天\n笑声回荡\n蔚蓝天空在身旁",
    "audio_url": "https://cdn.acedata.cloud/assets/examples/fish/5ade0339-5f11-487e-aacc-06a908271706-8e3fcb0e5547.mp3"
  }
}
```

可以看到，`data` 的 `audio_id` 字段就是上传后的歌曲 ID。

有了歌曲 ID 之后，我们便可以使用 [Producer Audios Generation API](https://platform.acedata.cloud/documents/producer-audios-integration) 来进行自定义歌曲生成了，比如说 `action` 传入 `upload_extend`，同时 `audio_id` 传入返回的歌曲 ID，就可以根据参考音频生成新的歌曲了。
