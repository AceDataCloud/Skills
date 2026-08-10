---
name: face-transform
description: Analyze and transform faces via AceDataCloud API. Use when detecting face keypoints, beautifying portraits, aging/de-aging faces, swapping genders, replacing faces between photos, creating cartoon avatars, or detecting liveness. Provides 7 specialized face APIs.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Face Transform

Analyze and transform faces through AceDataCloud's Face API suite.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/face/analyze \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/portrait.jpg"}'
```

## Available APIs

| Endpoint | Purpose | Description |
|----------|---------|-------------|
| `POST /face/analyze` | Face Detection | Detect face keypoints (90+ points per face) |
| `POST /face/beautify` | Beautification | Apply beauty/decoration effects |
| `POST /face/change-age` | Age Transform | Make a face look older or younger |
| `POST /face/change-gender` | Gender Swap | Transform facial gender characteristics |
| `POST /face/swap` | Face Swap | Replace one person's face with another |
| `POST /face/cartoon` | Cartoon Style | Convert portrait to animated/cartoon style |
| `POST /face/detect-live` | Liveness Check | Detect if a face image is from a live person |

## Workflows

### 1. Face Analysis

Detect faces and extract 90+ keypoints per face.

```json
POST /face/analyze
{
  "image_url": "https://example.com/photo.jpg"
}
```

Response includes `face_shape_set` as an array of face keypoint objects. Each object can contain `nose`, `mouth`, `left_eye`, `right_eye`, `left_eyebrow`, `right_eyebrow`, and `contour` arrays of `{x, y}` coordinates.

### 2. Face Beautification

```json
POST /face/beautify
{
  "image_url": "https://example.com/portrait.jpg"
}
```

### 3. Age Transformation

`age_infos` is required — one entry per face, each carrying the target `age`.

```json
POST /face/change-age
{
  "image_url": "https://example.com/portrait.jpg",
  "age_infos": [{ "age": 60 }]
}
```

### 4. Gender Swap

`gender_infos` is required. `gender` is `0` to turn a male face female, `1` for the reverse.

```json
POST /face/change-gender
{
  "image_url": "https://example.com/portrait.jpg",
  "gender_infos": [{ "gender": 1 }]
}
```

### 5. Face Swap

Replace the face in the target image with the face from the source.

```json
POST /face/swap
{
  "source_image_url": "https://example.com/source-face.jpg",
  "target_image_url": "https://example.com/target-person.jpg"
}
```

### 6. Cartoon Style

```json
POST /face/cartoon
{
  "image_url": "https://example.com/portrait.jpg"
}
```

### 7. Liveness Detection

```json
POST /face/detect-live
{
  "image_url": "https://example.com/face-photo.jpg"
}
```

The liveness response includes numeric `score` plus `face_model_version`.

## Parameters

### Common

| Parameter | Required | Description |
|-----------|----------|-------------|
| `image_url` | Yes (all except `/face/swap`) | Source face image URL |

### `/face/change-age`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `age_infos` | Yes | Array of `{ "age": <number> }`, one per face. Omitting it returns `400 age_infos is required` |

### `/face/change-gender`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `gender_infos` | Yes | Array of `{ "gender": 0\|1 }` — `0` male→female, `1` female→male. Each entry also accepts an optional `face_rect` |

### `/face/swap`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `source_image_url` | Yes | URL of the face to use (replaces the face) |
| `target_image_url` | Yes | URL of the image to put the face onto |
| `callback_url` | No | Webhook URL for async delivery |
| `timeout` | No | Max wait time in seconds (default: 120) |

### `/face/beautify`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `image_url` | Yes | Image URL |
| `smoothing` | No | Skin smoothing 0–100 (default: 10) |
| `whitening` | No | Whitening 0–100 (default: 30) |
| `face_lifting` | No | Face slimming 0–100 (default: 70) |
| `eye_enlarging` | No | Eye enlarging 0–100 (default: 70) |

### `/face/analyze`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `image_url` | Yes | Image URL |
| `mode` | No | `0` = all faces (default), `1` = largest face only |
| `face_model_version` | No | Algorithm version (recommended: `3.0`) |
| `need_rotate_detection` | No | `0` = disabled (default), `1` = enabled |

## Gotchas

- All face APIs return results synchronously. `/face/swap` additionally supports an optional `callback_url` parameter for async delivery (pass it to receive the result via webhook instead of waiting inline)
- Face analyze returns 90+ keypoints per detected face, supporting multiple faces in one image
- Treat `face_shape_set` as an array, not a string; each entry describes one detected face
- Face swap uses `source_image_url` (the face to apply) and `target_image_url` (the body to apply it to)
- All APIs are currently in **Alpha** stage — interfaces may evolve
- Images should contain clearly visible, front-facing faces for best results
- Liveness detection helps distinguish live photos from printed/screen photos
