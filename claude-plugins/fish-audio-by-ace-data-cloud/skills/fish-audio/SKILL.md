---
name: fish-audio
description: Convert text to speech with a selected voice and retrieve existing audio task results through Ace Data Cloud.
license: Apache-2.0
---

# Fish Audio in Claude Code

Read the speech usage guide, then synthesize the text and voice explicitly chosen by the user. An existing task can be retrieved without submitting another speech request. The input text is sent to Ace Data Cloud when generation is requested.

1. If setup is needed, point the user to [Applications](https://platform.acedata.cloud/console/applications?utm_source=claude&utm_medium=referral&utm_campaign=evergreen) and the masked **Ace Data Cloud API Token** field under this plugin’s **Configure options**. Keep the token out of the conversation.
2. Call `fish_get_usage_guide` for a read-only reference check. It returns local usage information without synthesizing audio.
3. Use `fish_generate_audio` for requested speech. If it returns a pending task ID, use `fish_get_task` with that ID until the service returns an audio URL or a terminal failure. Use the connected tool’s input schema for parameter names and supported values. Run billed operations only when the user requested the operation and supplied the inputs. [Service pricing](https://platform.acedata.cloud/models?utm_source=claude&utm_medium=referral&utm_campaign=evergreen).
