# Producer 歌词生成接口 API 对接说明

Producer 允许我们通过提示词来生成歌词，本文档讲解相关 API 的对接方法。

该 API 只有一个输入参数，就是 `prompt`，它是生成歌词的提示词。

这里我们输入的 `prompt` 是 `A song about winter`，是生成歌词的提示词。

```bash
curl -X POST 'https://api.acedata.cloud/producer/lyrics' \
-H 'accept: application/json' \
-H 'authorization: Bearer {token}' \
-H 'content-type: application/json' \
-d '{
  "prompt": "A song about winter"
}'
```

结果如下：

```
{
    "success": true,
    "task_id": "d354b519-43c0-4888-a3da-83adbf845fd6",
    "data": {
        "title": "Mercy in the Trees",
        "lyrics": "[Verse 1]\nI walked out past the railyard\nWhere the pines grow thick with frost\nThe snow doesn't care what I've done\nIt covers everything the same\n\n[Verse 2]\nThere's a chapel made of birch trunks\nAnd the altar is the ground\nI kneel there like a traitor\nWaiting for the silence to forgive\n\n[Chorus]\nWinter is a heavy coat\nWinter is a heavy coat\n\n[Verse 3]\nYou left before the first storm\nI stayed to watch the world go white\nNow every branch is a bone\nAnd I'm just counting what remains\n\n[Verse 4]\nThey say the cold will kill you\nBut I think it just makes you honest\nOut here with the frozen earth\nThere's nowhere left to hide your hands\n\n[Chorus]\nWinter is a heavy coat\nWinter is a heavy coat\n\n[Verse 5]\nI found your letter in my pocket\nThe ink had bled from all the thaw\nBut I could still read mercy\nWritten in the empty space between\n\n[Outro]\nThe trees don't ask for absolution\nThey just stand there, bare and true\nI'm learning how to do the same\nLetting the snow bury what it needs to bury"
    }
}
```

可以看到，`data` 的 `lyrics` 字段就是生成的歌词内容。
