---
name: acedatacloud-api
description: Guide for using AceDataCloud APIs. Use when authenticating, making API calls, managing credentials, understanding billing, or integrating AceDataCloud services into applications. Covers setup, authentication, request patterns, error handling, and SDK integration.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires an AceDataCloud account at platform.acedata.cloud.
---

# AceDataCloud API Usage Guide

Complete guide for using AceDataCloud's AI-powered data services API.

## Getting Started

### 1. Create an Account

Register at [platform.acedata.cloud](https://platform.acedata.cloud).

### 2. Subscribe to a Service

Browse available services and click **Get** to subscribe. Most services include free quota.

### 3. Create API Credentials

Go to your service's **Credentials** page and create an API Token.

> **Full details:** See [authentication](../_shared/authentication.md) for token types and usage.

## SDK Integration (OpenAI-Compatible)

For chat completion services, use the standard OpenAI SDK:

```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_TOKEN",
    base_url="https://api.acedata.cloud/v1"
)

response = client.chat.completions.create(
    model="claude-sonnet-4-20250514",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

```javascript
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: "YOUR_API_TOKEN",
  baseURL: "https://api.acedata.cloud/v1"
});

const response = await client.chat.completions.create({
  model: "gpt-4.1",
  messages: [{ role: "user", content: "Hello!" }]
});
```

## Request Patterns

### Synchronous APIs

Some APIs return results immediately (e.g., face transform, search):

```bash
curl -X POST https://api.acedata.cloud/face/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/photo.jpg"}'
```

### Async Task APIs

Most generation APIs (images, video, music) are asynchronous.

> **Full details:** See [async task polling](../_shared/async-tasks.md) for the submit-and-poll pattern.

## Error Handling

| HTTP Code | Meaning | Action |
|-----------|---------|--------|
| 400 | Bad request | Check request parameters |
| 401 | Unauthorized | Check API token |
| 403 | Forbidden | Content filtered or insufficient permissions |
| 429 | Rate limited | Wait and retry with backoff |
| 500 | Server error | Retry or contact support |

Error response format:

```json
{
  "error": {
    "code": "token_mismatched",
    "message": "Invalid or expired token"
  }
}
```

## Billing

- Each API call deducts from your **subscription balance** (remaining_amount)
- Cost varies by service, model, and usage (tokens, requests, data size)
- Check balance at [platform.acedata.cloud](https://platform.acedata.cloud)
- Most services offer free trial quota

## Service Categories

| Category | Services | Base Path |
|----------|----------|-----------|
| **AI Chat** | GPT, Claude, Gemini, DeepSeek, Grok | `/v1/chat/completions` |
| **Image Gen** | Midjourney, Flux, Seedream, NanoBanana | `/midjourney/*`, `/flux/*`, etc. |
| **Video Gen** | Luma, Sora, Veo, Kling, Hailuo, Seedance, Wan | `/luma/*`, `/sora/*`, etc. |
| **Music Gen** | Suno, Producer, Fish Audio | `/suno/*`, `/producer/*`, `/fish/*` |
| **Search** | Google Search (web/images/news/maps) | `/serp/*` |
| **Face** | Analyze, beautify, swap, cartoon, age | `/face/*` |
| **Utility** | Short URL, QR Art, Headshots | `/short-url`, `/qrart/*`, `/headshots/*` |

## Gotchas

- Tokens are **service-scoped** by default — create a global token if you need cross-service access
- Async APIs return a `task_id` — always use `callback_url` to get the task_id immediately, then poll for results
- Avoid `wait: true` — it blocks for the full generation duration and will time out for video/music tasks
- Rate limits vary by service tier — upgrade your plan if hitting limits
- All timestamps are in UTC

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration with AI agents.
