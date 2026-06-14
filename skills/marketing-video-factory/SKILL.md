---
name: marketing-video-factory
description: Produce a short-form (9:16, ~30-60s) marketing / feature-explainer video end-to-end using AceDataCloud's own AI APIs — generate B-roll + hero images (Flux/Seedream/NanoBanana/Seedance), a music bed (Suno) and voiceover (TTS), capture real product UI with Playwright, assemble with FFmpeg (burned-in captions), upload to CDN, then distribute. Use when the user wants to make a promo/feature/explainer video, a TikTok/Reels/Shorts/Bilibili/Douyin short, "automated video marketing", or to turn a product feature into a vertical video.
when_to_use: |
  Trigger when the user wants to PRODUCE a finished short-form video
  (not just call one model): a marketing/feature/promo/explainer short,
  a vertical video for TikTok / YouTube Shorts / Reels / Bilibili /
  Douyin / X / LinkedIn, or an "automated video factory". This skill is
  the playbook that orchestrates the single-service skills
  (flux-image, seedream-image, nano-banana-image, seedance-video,
  veo-video, suno-music, fish-audio, short-url) into one pipeline.
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN (model calls) and ACEDATACLOUD_PLATFORM_TOKEN (CDN upload) in .env (see _shared/authentication.md). Needs ffmpeg, python3 + pillow, and (for screenshots) playwright. Optionally pair with the per-service MCP servers (_shared/mcp-servers.md).
---

# Marketing Video Factory

Turn a product feature into a platform-ready vertical short, made **with the same
AI APIs you're advertising** (so the video is also a live demo of itself).

> **Setup:** [authentication](../_shared/authentication.md) · async behavior:
> [async task polling](../_shared/async-tasks.md) · tool-use: [MCP servers](../_shared/mcp-servers.md).

## Strategy (read first)

1. **Dogfood.** Generate every asset through `api.acedata.cloud` (Flux, Seedream,
   NanoBanana, Seedance/Veo, Suno, TTS). The output *is* the proof.
2. **Real UI is the spine; AI footage is the spice.** For a software/dev product,
   show real screen-captures/screenshots of the product for the demo beats;
   reserve AI-generated clips for intro / atmosphere / transitions. AI models
   hallucinate fake buttons/code → never use them to depict the actual product.
3. **Structure every video:** `Hook (0-3s) → Value (4-15s) → Demo (16-50s) →
   CTA (last ~5s)`. One cut every 2-4s. Captions always on (≈85% watch muted).

## Workflow

1. **Brief** the feature: pull real value-prop copy from your docs (verbatim
   on-screen text beats invented copy).
2. **Script** a Scene-JSON: per scene = `{visual, duration, caption}`, following
   the hook→value→demo→CTA skeleton.
3. **Generate assets** (async — submit then poll): hero/B-roll images, B-roll
   clips, a music bed, voiceover. Use `watermark=false`. Pin aspect to 9:16.
4. **Capture UI** screenshots with Playwright (mobile 9:16 viewport).
5. **Assemble** with FFmpeg: per-scene render → concat → mix music. Burn captions.
6. **Upload** the final MP4 to the CDN; **distribute** per platform.

## Recipe — generate an asset (submit + poll)

```bash
# Hero / B-roll image. Flux & NanoBanana honor true 9:16; Seedream size is an
# ENUM (1K/2K/...) and tends to return 16:9 — use Flux for vertical heroes.
curl -sS -X POST https://api.acedata.cloud/flux/images \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" -H "Content-Type: application/json" \
  -d '{"model":"flux-2-pro","prompt":"<scene visual>, deep violet/indigo, cinematic, no text","size":"9:16"}'

# B-roll clip (Seedance is fast/cheap; Veo for hero quality). watermark off.
curl -sS -X POST https://api.acedata.cloud/seedance/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" -H "Content-Type: application/json" \
  -d '{"model":"doubao-seedance-2-0-fast-260128","content":[{"type":"text","text":"<motion>, 9:16, no text"}],"resolution":"720p","ratio":"9:16","duration":5,"watermark":false}'

# Music bed — instrumental (see suno-music). Then poll /suno/tasks.
curl -sS -X POST https://api.acedata.cloud/suno/audios \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" -H "Content-Type: application/json" \
  -d '{"action":"generate","prompt":"uplifting minimal electronic, premium tech","instrumental":true,"model":"chirp-v5-5"}'
```

All of the above return a `task_id` — **poll the matching `/<service>/tasks`** until
`state`/`status` is terminal, then read the media URL (see _shared/async-tasks.md).
The media is served from `*.cdn.acedata.cloud`. Per-model details: `flux-image`,
`seedream-image`, `nano-banana-image`, `seedance-video`, `veo-video`, `suno-music`,
`fish-audio` skills. (Voiceover: `POST /text-to-speech`, keep word timings for
karaoke captions.)

## Recipe — capture product UI (Playwright)

```python
# pip install playwright && python -m playwright install chromium
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    # 9:16 viewport so a vertical video doesn't center-crop a desktop layout.
    ctx = b.new_context(viewport={"width":1080,"height":1920}, device_scale_factor=2,
                        storage_state="auth.json")  # omit for public pages
    pg = ctx.new_page(); pg.goto(URL, wait_until="networkidle"); pg.wait_for_timeout(3500)
    pg.screenshot(path="shot.png")
```

**Public marketing pages capture anonymously; logged-in console/app pages need a
saved `storage_state`** (a throwaway demo account) — without it they redirect to
the login wall.

## Recipe — assemble (per-scene render → concat → music)

Do **NOT** build one giant filtergraph with all inputs — with several hi-res
images + caption PNGs it OOMs ("Cannot allocate memory"). Render each scene
to an intermediate, then concat (stream-copy), then mux music:

```bash
W=1080; H=1920; FPS=30
SCALE="scale=$W:$H:force_original_aspect_ratio=increase,crop=$W:$H,setsar=1,fps=$FPS"

# Per scene: a still (loop to DUR) or a clip (trim to DUR) + a transparent
# caption PNG overlaid. Produce identical-codec segNN.mp4 (no audio).
ffmpeg -y -loop 1 -t $DUR -i still.png  -loop 1 -i capNN.png \
  -filter_complex "[0:v]$SCALE[bg];[bg][1:v]overlay=0:0:shortest=1[v]" \
  -map "[v]" -an -t $DUR -c:v libx264 -pix_fmt yuv420p -r $FPS \
  -video_track_timescale 15360 segNN.mp4
# (for a clip scene: replace "-loop 1 -t $DUR -i still.png" with "-i clip.mp4")

# Concat (all segments share codec/params) + mix music under, with a fade-out.
printf "file 'seg00.mp4'\nfile 'seg01.mp4'\n..." > segs.txt
ffmpeg -y -f concat -safe 0 -i segs.txt -c copy video_silent.mp4
ffmpeg -y -i video_silent.mp4 -i music.mp3 \
  -filter_complex "[1:a]volume=-3dB,afade=t=out:st=$(($TOTAL-1)):d=1[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -shortest one-api-key.mp4
```

Captions: render each as a **transparent PNG** (Pillow) and overlay — portable
across all ffmpeg builds (avoids the libfreetype `drawtext` dependency). Use a
real bold sans (`C:/Windows/Fonts/arialbd.ttf`, `DejaVuSans-Bold.ttf`, etc.),
3-7 words/line, white + black stroke; push to the **upper third during UI demos**
so the product stays visible.

> Reference implementation (Scene-JSON contract, caption-burn, render driver,
> material-library convention): **AceDataCloud/PlatformStudio** (`app/`,
> `scripts/build_video.py`, `assets/MATERIALS.md`).

## Recipe — upload to CDN + distribute

```bash
curl -sS -X POST https://platform.acedata.cloud/api/v1/files/ \
  -H "Authorization: Bearer $ACEDATACLOUD_PLATFORM_TOKEN" \
  -F "file=@one-api-key.mp4"   # -> {"file_url":"https://cdn.acedata.cloud/....mp4"}
```

Distribute with a short link (`short-url` skill) + per-platform metadata. Author
once at 1080×1920 inside a centered 900×1400 safe box, then atomize to 16:9 / 1:1.

## Creative cheat-sheet

- **Length:** TikTok 15-34s · Shorts/Reels 30-60s · X <60s · LinkedIn 30-90s.
- **Captions:** always on, karaoke word-highlight, avoid bottom ~20-25% & right edge.
- **Audio:** final mix ≈ **−14 LUFS**, music **15-20 dB under** voice; sidechain-duck
  (`sidechaincompress`) the music off the narration; `loudnorm=I=-14:TP=-1:LRA=11`.
- **CTA:** one clear visual CTA in the last ~5s (assume muted).

## Gotchas

- **Generation is async** — every model call returns a `task_id`; poll the
  service's `/tasks` endpoint. Don't treat the first response as the result.
- **Aspect:** pin 9:16 explicitly. `seedream` `size` is an enum (1K/2K/3K/4K) and
  skews 16:9 → use **Flux** (`size:"9:16"`) or **NanoBanana** (`aspect_ratio`) for
  true vertical heroes.
- **`watermark:false`** on marketing assets (Seedance/Seedream default to true).
- **Single mega-filtergraph OOMs** on multi-input hi-res jobs → render per-scene
  then `concat -c copy` (above).
- **Screenshots:** use a **9:16 viewport** (not a desktop one center-cropped);
  logged-in pages need a saved Playwright `storage_state`.
- **CDN download SSL:** some hosts (e.g. `cdn1.suno.ai`) fail Python `urllib`
  cert verification → fetch with `curl -L` instead.
- **Music licensing:** Suno free tier is **non-commercial**; paid plans give no
  indemnification → for **paid ads** use a fully-licensed library; keep Suno for
  organic. Master to −14 LUFS regardless.
- **Don't hard-couple the video model** — keep it swappable (Veo/Seedance/Luma);
  abstract the provider so a deprecation (e.g. a Sora API sunset) is a 1-line change.
- **Cross-posting:** strip watermarks before re-uploading; rewrite title/hashtags
  per platform; keep Instagram reposts <10 / 30 days; use a humane cadence (bursts
  read as spam).
