---
name: seedream
description: Generate or edit Seedream images from a prompt and selected reference images through Ace Data Cloud.
license: Apache-2.0
---

# Seedream in Claude Code

Generate an image from the user’s prompt, or edit the specific reference images the user selected. Start with the requested model and dimensions, using the live tool schema for supported settings.

1. If setup is needed, sign in to [Applications](https://platform.acedata.cloud/console/applications?utm_source=claude&utm_medium=referral&utm_campaign=evergreen) and open **General Application**. If it is missing, choose **Initialize General Application**. Click the copy button marked **1** next to **API KEY**. Enter the raw key in the Claude Code plugin’s private **Ace Data Cloud API Token** field. In Claude Code, open **/plugin → Installed → Configure options** to enter it. Keep the token out of the conversation.

   ![Copy button 1 beside the General Application API key](https://raw.githubusercontent.com/AceDataCloud/NanoBananaDify/2522b2f57210597af2db866445319334a1677a23/_assets/tutorial/get-api-key-en.png)

2. Call `seedream_list_models` for a read-only reference check. It shows the supported models from local reference data.
3. Use `seedream_generate_image` for a new image and `seedream_edit_image` for an explicitly selected reference. Check a pending result with `seedream_get_task` using the original ID. Use the connected tool’s input schema for parameter names and supported values. Run billed operations only when the user requested the operation and supplied the inputs. [Service pricing](https://platform.acedata.cloud/models?utm_source=claude&utm_medium=referral&utm_campaign=evergreen).
