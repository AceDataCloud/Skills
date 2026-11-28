---
name: google-search
description: Search web, news, images, places, videos and maps through your Ace Data Cloud search application.
license: Apache-2.0
---

# Google Search in Claude Code

Search the web for a topic and return a small set of source links. Choose the specialized image, news, video, place or map tool only when the user asks for that content. Keep search terms to the user-provided topic and present links alongside the findings.

1. If setup is needed, sign in to [Applications](https://platform.acedata.cloud/console/applications?utm_source=claude&utm_medium=referral&utm_campaign=evergreen) and open **General Application**. If it is missing, choose **Initialize General Application**. Click the copy button marked **1** next to **API KEY**. Enter the raw key in the Claude Code plugin’s private **Ace Data Cloud API Token** field. In Claude Code, open **/plugin → Installed → Configure options** to enter it. Keep the token out of the conversation.

   ![Copy button 1 beside the General Application API key](https://raw.githubusercontent.com/AceDataCloud/NanoBananaDify/2522b2f57210597af2db866445319334a1677a23/_assets/tutorial/get-api-key-en.png)

2. Call `serp_list_search_types` for a read-only reference check. It displays the available search types from local reference data.
3. Pass the requested query and locale to `serp_google_search`. Read the output URLs directly. Use the connected tool’s input schema for parameter names and supported values. Run billed operations only when the user requested the operation and supplied the inputs. [Service pricing](https://platform.acedata.cloud/models?utm_source=claude&utm_medium=referral&utm_campaign=evergreen).
