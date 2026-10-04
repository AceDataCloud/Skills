<!-- Generated from PlatformBackend; edit the backend source. -->
# API reference

These are the public HTTP API contracts. Native MCP tools and CLI commands are described in the package README.

## Kling video generation

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/kling/motion` | `model_name`, `mode`, `keep_original_sound`, `watermark_info`, `image_url`, `video_url`, `character_orientation`, `prompt`, `callback_url`, `async` |
| POST | `/kling/tasks` | `id`, `ids`, `action` |
| POST | `/kling/videos` | `mode`, `model`, `action`, `prompt`, `duration`, `generate_audio`, `video_id`, `cfg_scale`, `aspect_ratio`, `callback_url`, `async`, `end_image_url`, `camera_control`, `image_list`, `video_list`, `negative_prompt`, `start_image_url`, `multi_shot`, `shot_type`, `multi_prompt`, `element_list`, `voice_list` |
| POST | `/kling/lip-sync` | `video_id`, `video_url`, `mode`, `audio_url`, `audio_type`, `audio_file`, `text`, `voice_id`, `voice_language`, `voice_speed`, `callback_url`, `async` |
| POST | `/kling/talking-photo` | `image_url`, `audio_url`, `prompt`, `model`, `duration`, `mode`, `callback_url`, `async` |
| POST | `/kling/goods-studio` | `contents`, `settings`, `watermark`, `async`, `callback_url` |
| POST | `/kling/video-commerce` | `contents`, `settings`, `watermark`, `async`, `callback_url` |

Full schema: [kling.json](openapi/kling.json).

### Guides

- [development_kling_goods_studio.md](guides/development_kling_goods_studio.md)
- [development_kling_lip_sync.md](guides/development_kling_lip_sync.md)
- [development_kling_motion.md](guides/development_kling_motion.md)
- [development_kling_talking_photo.md](guides/development_kling_talking_photo.md)
- [development_kling_tasks.md](guides/development_kling_tasks.md)
- [development_kling_video_commerce.md](guides/development_kling_video_commerce.md)
- [development_kling_videos.md](guides/development_kling_videos.md)

Source: [PlatformBackend@945664eca88d](https://github.com/AceDataCloud/PlatformBackend/tree/945664eca88d16d21159d3739f874c830c046005).
