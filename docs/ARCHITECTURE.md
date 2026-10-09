# Architecture

Two independent parts with one contract between them:

```
 web/ (Vue 3 + TS)  ──HTTP /api/v1 (OpenAPI)──▶  engine/ (Python package `sleng`)
                                                   ▲            ▲
                                Python callers ────┘            └──── `sleng` CLI
```

The engine knows nothing about the UI. The UI knows nothing about models, ffmpeg or files:
every list it shows (voices, base voices, themes, palettes, sizes, cleanup levels) and every rule
it relies on (the pause after a line) comes from the engine.

## Engine layers

Imports only point downwards; import-linter fails the commit otherwise.

```
adapters    http (FastAPI)  ·  cli (argparse)        translate in → one service call → translate out
container   Sleng: builds every object once           the composition root and Python API
config      Settings (defaults < SLENG_* env < overrides)
services    SpeechService · ExportService · VideoService · VoiceService · JobManager
voices      VoiceRegistry · VoiceFactory · MmsVoice · EdgeVoice · FakeVoice · Cached/CleanedVoice
cloning | media     ToneConverter, CloneStore, ClonedVoice | subtitles, ASS, scenes, renderer, pop art
audio | text        polish, loudness, merge, cleanup, WAV | numbers, normalise, split
infra       Ffmpeg runner · LruCache · require() for optional packages
domain      Audio, Timeline, Chunk, Script, options, requests, errors, voice catalog, VoiceEngine
```

### Key design choices

| Choice | Why |
|---|---|
| `VoiceEngine` is a Protocol; engines are composed, not inherited | MMS, Edge, fake and cloned voices share nothing but `synthesize()` |
| `CachedVoice(CleanedVoice(CachedVoice(raw)))` per (voice, cleanup) | one cache implementation; switching cleanup never re-synthesizes |
| `Audio` carries its sample rate | no code can mix samples with the wrong rate |
| Video looks are `Scene` strategies on a `FilterGraph` builder | a new look is one class, no edits to the renderer |
| Long renders are jobs with progress | the HTTP request returns at once; the UI polls; ready for a real queue |
| `SlengError` subclasses map to HTTP statuses in one place | every error reaches the UI as `{"error", "type"}` |
| Heavy libraries import lazily via `require()` | `import sleng` stays fast; missing extras give an install command |

## Request flows

**Speak (UI).** `POST /text/split` → lines. For each line the UI calls `POST /speech/line`
(producer) while playing finished lines (consumer, `ClipQueue`). The response header
`X-Gap-After` says how long to wait before the next line, so the pause rule lives only in
`PauseOptions.gap_after`.

**Video.** `POST /jobs/video` (202 + job) → `JobManager` thread runs `VideoService.render`:
narrate (0–40 %), build ASS captions, paint the scene, stream voice-bar frames into ffmpeg
(40–100 %). The UI polls `GET /jobs/{id}` and downloads `GET /jobs/{id}/result`
(`X-Seed` = design number).

## Extension points

| To add | Touch |
|---|---|
| A voice engine (e.g. Azure, Piper) | new class in `voices/`, a branch in `VoiceFactory.create`, an entry in `domain/voice.py` |
| A video look | new `Scene` subclass in `media/scenes/`, one entry in `SCENES`, a `VideoTheme` value, i18n `th_<name>` |
| An endpoint | a router module in `adapters/http/routes/`, add it to `ROUTERS`; request/response models in `schemas/` |
| A CLI command | `adapters/cli/main.py` (arguments) + `adapters/cli/commands.py` (handler) |
| A UI language | `web/src/i18n/<code>.json` (typed against `en.json`) + `LOCALES` |

## Scaling up

- **More users / a server**: run `sleng serve` behind a reverse proxy that adds authentication and
  TLS. Raise `SLENG_JOB_WORKERS` for parallel renders. Keep `SLENG_DATA_DIR` on a volume.
- **Many machines**: keep the `JobManager` interface and back it with a real queue (RQ, Celery, a
  cloud task queue) plus shared storage for `voices/` and job results. Nothing above `services`
  changes.
- **GPU**: `SLENG_DEVICE=cuda` (MMS and the clone converter use it).

## Desktop app (Tauri)

1. `cd web && VITE_API_BASE=http://127.0.0.1:7860/api/v1 npm run build`
2. Freeze the engine with the package installed:
   `pyinstaller -n sleng-engine --collect-data sleng engine/src/sleng/__main__.py`
   (one-folder build), and register it as a Tauri sidecar started with
   `serve --no-browser --port 7860`.
3. Point Tauri at `web/dist`. The engine's default CORS origins already include the Tauri ones.
