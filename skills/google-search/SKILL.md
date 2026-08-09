---
name: google-search
description: Search the web using Google via AceDataCloud API. Use when searching for web pages, images, news, maps, local places, or videos. Supports localization, time filtering, and pagination. Returns structured results with titles, snippets, URLs, and rich data.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-serp for tool-use.
---

# Google Search (SERP)

Search the web through AceDataCloud's Google SERP API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/serp/google \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "latest AI news", "type": "search"}'
```

## Search Types

| Type | Description | Returns |
|------|-------------|---------|
| `search` | Web search (default) | Organic results, knowledge graph, rich snippets |
| `images` | Image search | Image URLs, titles, sources |
| `news` | News articles | Headlines, sources, publish dates |
| `maps` | Map results | Locations, coordinates |
| `places` | Local businesses/places | Name, address, rating, reviews |
| `videos` | Video results | Video URLs, thumbnails, duration |

## Parameters

```json
POST /serp/google
{
  "query": "your search query",
  "type": "search",
  "country": "us",
  "language": "en",
  "range": "qdr:w",
  "number": 10,
  "page": 1
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Required non-whitespace query, 1–2048 characters |
| `type` | string | One of: search, images, news, maps, places, videos (default `search`) |
| `country` | string | Country code, 1–32 characters (e.g., "us", "uk", "cn", "jp") |
| `language` | string | Language code, 1–32 characters (e.g., "en", "zh", "ja") |
| `range` | string | Time filter (see below) |
| `number` | int | Results per page, 1–100 (default 10) |
| `page` | int | Page number, 1–100 (default 1) |
| `image_size` | string | **Requires `type: "images"`**. Filter by size: `large`, `medium`, `icon`, or `2mp`, `4mp`, `6mp`, `8mp`, `10mp`, `12mp`, `15mp`, `20mp`, `40mp`, `70mp`. |

## Time Range Options

| Value | Period |
|-------|--------|
| `qdr:h` | Past hour |
| `qdr:d` | Past 24 hours |
| `qdr:w` | Past week |
| `qdr:m` | Past month |
| `qdr:y` | Past year |

The equivalent short values `h`, `d`, `w`, `m`, and `y` are also accepted.

## Response Structure

Web search returns structured data including:
- `organic`: Main search results with title, link, snippet
- `knowledge_graph`: Entity information panel (when available)
- `related_searches`: Related query suggestions

## Gotchas

- Default search type is `"search"` (web). Always specify `type` for non-web searches
- Country and language codes affect result localization significantly
- `number` controls results per page, not total results — use `page` for pagination
- Time range (`range`) only applies to web search and news, not images or places
- **Image resolution (important for video / full-screen use):** image results provide `image_url`. Pass **`image_size: "large"`** (or a megapixel minimum like `"4mp"`) to request sharper sources.
- Places search works best with location-specific queries (e.g., "restaurants near Times Square")

> **MCP:** `pip install mcp-serp` | Hosted: `https://serp.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
