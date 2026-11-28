---
name: fish-audio
description: Convert text to speech with a selected voice and retrieve existing audio task results through Ace Data Cloud.
license: Apache-2.0
---

# Fish Audio in Claude Code

Read the speech usage guide, then synthesize the text and voice explicitly chosen by the user. An existing task can be retrieved without submitting another speech request. The input text is sent to Ace Data Cloud when generation is requested.

1. If setup is needed, sign in to [Applications](https://platform.acedata.cloud/console/applications?utm_source=claude&utm_medium=referral&utm_campaign=evergreen) and open **General Application**. If it is missing, choose **Initialize General Application**. Click the copy button marked **1** next to **API KEY**. Enter the raw key in the Claude Code plugin’s private **Ace Data Cloud API Token** field. In Claude Code, open **/plugin → Installed → Configure options** to enter it. Keep the token out of the conversation.

   ![Copy button 1 beside the General Application API key](https://raw.githubusercontent.com/AceDataCloud/NanoBananaDify/2522b2f57210597af2db866445319334a1677a23/_assets/tutorial/get-api-key-en.png)

2. Call `fish_get_usage_guide` for a read-only reference check. It returns local usage information without synthesizing audio.
3. Use `fish_generate_audio` for requested speech. If it returns a pending task ID, use `fish_get_task` with that ID until the service returns an audio URL or a terminal failure. Use the connected tool’s input schema for parameter names and supported values. Run billed operations only when the user requested the operation and supplied the inputs. [Service pricing](https://platform.acedata.cloud/models?utm_source=claude&utm_medium=referral&utm_campaign=evergreen).
