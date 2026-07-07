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
| `query` | string | Search query (required) |
| `type` | string | One of: search, images, news, maps, places, videos |
| `country` | string | Country code (e.g., "us", "uk", "cn", "jp") |
| `language` | string | Language code (e.g., "en", "zh", "ja") |
| `range` | string | Time filter (see below) |
| `number` | int | Number of results per page |
| `page` | int | Page number for pagination |
| `image_size` | string | **Images only.** Filter by size for high-res sources: `large` / `medium` / `icon`, or a megapixel minimum `2mp`…`70mp` (e.g. `4mp` = larger than 4 megapixels). Use `large` (or a `*mp` value) whenever the image will be shown large / full-screen / zoomed. |

## Time Range Options

| Value | Period |
|-------|--------|
| `qdr:h` | Past hour |
| `qdr:d` | Past 24 hours |
| `qdr:w` | Past week |
| `qdr:m` | Past month |
| `qdr:y` | Past year |

## Response Structure

Web search returns structured data including:
- `organic_results`: Main search results with title, link, snippet
- `knowledge_graph`: Entity information panel (when available)
- `related_searches`: Related query suggestions

## Gotchas

- Default search type is `"search"` (web). Always specify `type` for non-web searches
- Country and language codes affect result localization significantly
- `number` controls results per page, not total results — use `page` for pagination
- Time range (`range`) only applies to web search and news, not images or places
- **Image resolution (important for video / full-screen use):** results include `image_url` (full-size), `thumbnail_url`, and `image_width`/`image_height`. Pass **`image_size: "large"`** (or a megapixel minimum like `"4mp"`) to get sharp sources, and pick the result with the largest `image_width`×`image_height`. Always download `image_url` — **never** use `thumbnail_url` as a final asset (it is tiny and blurry).
- Places search works best with location-specific queries (e.g., "restaurants near Times Square")

> **MCP:** `pip install mcp-serp` | Hosted: `https://serp.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
