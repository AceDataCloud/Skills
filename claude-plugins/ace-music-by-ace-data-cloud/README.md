# ACE Music by Ace Data Cloud

Independently installable ACE Music song and lyrics tools, using your own Ace Data Cloud API account. API/package/hosted deployment availability are separate release checks; this source package does not prove a live release.

## API key

[Sign in or register](https://platform.acedata.cloud/?utm_source=github&utm_medium=referral&utm_campaign=evergreen&utm_content=ace_music_plugin_signup) → [Applications](https://platform.acedata.cloud/console/applications?utm_source=github&utm_medium=referral&utm_campaign=evergreen&utm_content=ace_music_plugin_api_key) → create a dedicated API key with ACE Music generation, lyrics and task-query access. Confirm the application balance and [current service price](https://platform.acedata.cloud/services/024e09b4-52cf-5e98-a91a-efedf43104c4?utm_source=github&utm_medium=referral&utm_campaign=evergreen&utm_content=ace_music_plugin_pricing). Enter the raw key in the plugin's sensitive API Token setting; do not include `Bearer ` or share it in chat.

![Application API key](assets/get-api-key-en.png)
![Create a dedicated key](assets/create-api-key-en.png)

These are existing Ace Data Cloud credential guide images; they are not new ACE Music generation evidence.

## Use

Ask to create a song from an idea, use supplied lyrics/style/title, or generate lyrics separately. Models are `acemusic-v1.1` and `acemusic-v1`; a task targets two MP3 candidates. Lyrics requests are separately priced. Upload, covers, continuation, voices, stems, WAV, MIDI and video export are not supported.

## Task recovery

Save the original task ID and query it roughly every 10 seconds. Only the group terminal state determines completion. Partial failure may include one downloadable song; report it as partial. On client timeout, retain the task ID for later recovery. If submission times out before a task ID arrives, reconcile the original request rather than automatically paying for a replacement.

This plugin source is self-contained. Official directory submission/approval, package publication and hosted service release require separate verification.
