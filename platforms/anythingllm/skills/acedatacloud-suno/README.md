# Suno

![Suno](https://raw.githubusercontent.com/AceDataCloud/SunoDify/318116be6aa8dcbdf23fa5aa9ff60f7a8571a0cc/_assets/icon.jpg)

Look up one existing Suno audio or lyrics task. The result includes its current status and any available outputs such as audio links or lyrics. The skill makes one lookup per invocation and never starts a new generation.

1. Import the skill and open **Settings → Agent Skills**.
2. Add an Ace Data Cloud token with access to the existing Suno task in the skill's password field, then enable the skill.
3. Ask `@agent Check the status of Suno task <your-task-id>.` Use the Ace Data Cloud task ID returned when the task was created.

If the task is pending or running, check again later with the same ID. Result links are returned to your AnythingLLM session.

[Get an API token](https://platform.acedata.cloud/console/applications?utm_source=anythingllm&utm_medium=referral&utm_campaign=evergreen&utm_content=suno) · [Suno Tasks API](https://platform.acedata.cloud/documents/suno-tasks?utm_source=anythingllm&utm_medium=referral&utm_campaign=evergreen&utm_content=suno)
