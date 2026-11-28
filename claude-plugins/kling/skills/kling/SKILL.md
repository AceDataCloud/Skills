---
name: kling
description: Create Kling videos from text or a reference image and retrieve results through Ace Data Cloud.
license: Apache-2.0
---

# Kling

Start with `kling_list_models` to inspect the installed model reference. For text or reference-image generation, use `kling_generate_video` or `kling_generate_video_from_image` only when the user requests it. For reference-image animation, pass the user-selected source image to the image workflow. Choose the model and options listed by the installed package. Return the original task ID and use `kling_get_task` to retrieve that task. Generation consumes Ace Data Cloud credits.

For setup, direct the user to [Applications](https://platform.acedata.cloud/console/applications?utm_source=claude&utm_medium=referral&utm_campaign=evergreen), the masked plugin token setting, and [current prices](https://platform.acedata.cloud/models?utm_source=claude&utm_medium=referral&utm_campaign=evergreen). Do not request the token in chat.

先用 `kling_list_models` 查看本地模型说明。生成前核对用户选择的模型、输入及费用，查询时沿用原任务 ID。参考图动画请使用用户选择的图片，并按包内模型说明选择受支持的参数。
