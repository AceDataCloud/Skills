---
name: veo
description: Create Veo videos from text or image frames and retrieve results through Ace Data Cloud.
license: Apache-2.0
---

# Veo

Start with `veo_list_models` to inspect the installed model reference. For text or reference-image generation, use `veo_text_to_video` or `veo_image_to_video` only when the user requests it. For image-to-video, use the number and order of reference frames required by the chosen model. Consult the built-in prompt guide for model-specific options. Return the original task ID and use `veo_get_task` to retrieve that task. Generation consumes Ace Data Cloud credits.

For setup, direct the user to [Applications](https://platform.acedata.cloud/console/applications?utm_source=claude&utm_medium=referral&utm_campaign=evergreen), the masked plugin token setting, and [current prices](https://platform.acedata.cloud/models?utm_source=claude&utm_medium=referral&utm_campaign=evergreen). Do not request the token in chat.

先用 `veo_list_models` 查看本地模型说明。生成前核对用户选择的模型、输入及费用，查询时沿用原任务 ID。参考帧的数量和顺序取决于模型，可查看包内提示词指南。
