# SLENG — guide for coding agents

Read [CODING_STANDARDS.md](CODING_STANDARDS.md) before editing. Hard limits, checked on commit:
**300 lines/file · 100 chars/line · 20 code lines/function · Purpose/Layer header on every file.**

## Where things live

| Task | Start here |
|---|---|
| Text splitting / numbers | `engine/src/sleng/text/` |
| A voice engine, caching, cleanup | `engine/src/sleng/voices/`, `engine/src/sleng/audio/cleanup.py` |
| Voice cloning | `engine/src/sleng/cloning/` |
| Subtitles, video looks, rendering | `engine/src/sleng/media/` (`scenes/`, `pop/`, `renderer.py`) |
| A use case (what the engine can do) | `engine/src/sleng/services/` |
| HTTP endpoints | `engine/src/sleng/adapters/http/routes/` + `schemas/` |
| CLI commands | `engine/src/sleng/adapters/cli/` |
| Wiring / settings | `engine/src/sleng/container.py`, `engine/src/sleng/config.py` |
| UI state and logic | `web/src/stores/` (components only render) |
| UI calls to the engine | `web/src/api/engine.ts` (the only HTTP code) |
| UI text | `web/src/i18n/en.json` + `km.json` (add every key to both) |

Layers and extension points: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Rules that are easy to break

- Engine imports point down only (`adapters → container → config → services → voices →
  cloning|media → audio|text → infra → domain`). A lower layer never imports a higher one.
- Keep `voices/<10 hex>/{ref.wav, se.pt, meta.json}` and `voices/_base/<id>.pt` readable:
  the user has saved clones in that format.
- Never import `openvoice.api` (it pulls in front-ends with old pins); only `openvoice.models`,
  `openvoice.utils`, `openvoice.mel_processing`.
- Voice engines must run in a thread without an event loop (EdgeVoice uses `asyncio.run`), so
  HTTP handlers that synthesize stay plain `def`, not `async def`.
- Seeded pop art keeps its random draw order so a design number recreates the same video.
- The web app never hard-codes engine knowledge (voices, palettes, sizes, pause rules).
