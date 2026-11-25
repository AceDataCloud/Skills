# Ace Data Cloud in Amp Model Routing

Checked 2026-10-18 against [official Model Routing](https://ampcode.com/docs/customize/model-routing) and current CLI `config model-providers add-router --help`.

Amp supports OpenAI Chat Completions, Responses, Anthropic Messages and Google GenAI through Custom URL. Its preset router choices are Ollama Cloud, OpenRouter, Vercel, Cloudflare, Google Cloud Agent Platform, Google AI Studio, Amazon Bedrock and OpenCode Go. Ace Data Cloud is not among the observed presets. The public plugin API registers tools/skills/modes but has no documented provider registration API. No public provider-preset contribution repository/form was found; this is an evidence gap, not proof Amp forbids a future integration.

A manually named Custom URL is available but does **not** meet the goal of selecting Ace from Amp's default provider menu. Do not add a mode or wrapper that pretends to create such a preset. A real preset needs Amp's provider implementation/catalog owner; retain a reviewable implementation brief: display name Ace Data Cloud; credential is an Ace service API token; select only exact supported model mappings and protocol; links to Applications/pricing; no wildcard fallback to other providers or Amp credits without user choice.

Do not use Check Access/check-access during an unbudgeted verification: exact-model validation may send inference. Account routing changes and live inference await an authorized Amp session and explicit scope. No model request was made for this package.
