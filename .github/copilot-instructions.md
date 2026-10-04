# Content and client synchronization

PlatformBackend is the source: customer guidance in `docs/`, API request and response contracts in `openapi/`, and public document membership in `cost/service_api_mapping.json`. Use the source commit recorded in each generated `source.json`. Docs is a presentation consumer.

Generated references are produced by PlatformBackend's `scripts/export_ecosystem_references.py`. Do not edit generated guide or schema copies. Update curated instructions, native commands/tools and tests when the public contract changes; generated reference freshness alone does not prove native wrapper parity. Keep withdrawn and undocumented endpoints out of public discovery. Preserve existing authentication, transport and task polling behavior.
