# SLENG – Khmer text-to-speech

Write a Khmer script, pick a voice (Microsoft neural, offline MMS-TTS, or a voice you cloned),
listen line by line, then export WAV, per-line WAVs, SRT subtitles or an MP4 video.

```
engine/   Python engine (package `sleng`): voices, cloning, audio, video. No UI code.
web/      Vue 3 + TypeScript interface. Talks to the engine over HTTP only.
docs/     ARCHITECTURE.md: layers, request flows, extension points, desktop + deploy.
```

The engine is usable on its own from Python, the command line, or HTTP; the web app is one client.

## Run it on your machine

```bash
python -m venv .venv
.venv\Scripts\activate                       # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt              # = pip install -e "engine[all,dev]"
pip install --no-deps https://github.com/myshell-ai/OpenVoice/archive/refs/heads/main.zip  # cloning

cd web && npm install && npm run build && cd ..
sleng serve                                  # opens http://127.0.0.1:7860
```

Run `sleng serve` from the repo root: it keeps your cloned voices in `./voices` and serves `./web/dist`.

**Working on the UI** (hot reload): `sleng serve --no-browser` in one terminal,
`cd web && npm run dev` in another, then open http://localhost:5173 (Vite proxies `/api`).

**No models or internet?** Add `--fake` to any command: voices become test tones.

## Use the engine from anything

**Python**

```python
from sleng import Sleng
from sleng.domain import NarrationRequest, Script, SpeechOptions

engine = Sleng()
wav = engine.exports.wav(NarrationRequest(Script(text="សួស្តី។"), SpeechOptions(voice="mms")))
```

**Command line**

```bash
sleng voices
sleng split  --file data/sample_long.txt
sleng speak  --file data/sample_long.txt --voice mms --out out.wav        # --format zip | srt
sleng video  --file data/sample_long.txt --theme pop --size 1080x1920 --out out.mp4
sleng openapi --out engine/openapi.json
```

**HTTP** (`sleng serve`; interactive docs at `/api/docs`, schema at `/api/openapi.json`)

| Method | Path (under `/api/v1`) | What |
|---|---|---|
| GET | `/health`, `/options` | liveness; themes, palettes, sizes, cleanup levels |
| GET / POST / DELETE | `/voices`, `/voices/{id}` | list; clone from an uploaded clip (multipart); delete |
| POST | `/voices/preview` | the clip as it would be cloned |
| POST | `/text/split` | lines with the pause after each |
| POST | `/speech/line` | one line as WAV; `X-Gap-After` header = pause before the next |
| POST | `/exports/wav`, `/exports/zip`, `/exports/srt` | whole-script downloads |
| POST / GET | `/jobs/video`, `/jobs/{id}`, `/jobs/{id}/result` | MP4 render in the background with progress |

Settings come from `SLENG_*` environment variables (see `engine/src/sleng/config.py`):
`SLENG_DATA_DIR`, `SLENG_DEVICE`, `SLENG_FAKE`, `SLENG_CORS_ORIGINS`, `SLENG_JOB_WORKERS`, …

## Desktop app and deployment

- **Docker**: `docker build -t sleng . && docker run -p 7860:7860 -v sleng-data:/data sleng`.
  There is no authentication: put it behind a reverse proxy with auth before exposing it.
- **Desktop** (Tauri): build the UI with `VITE_API_BASE=http://127.0.0.1:7860/api/v1 npm run build`,
  bundle the engine (e.g. PyInstaller) as a sidecar that runs `sleng serve --no-browser`.
  CORS already allows the Tauri origins. Details in `docs/ARCHITECTURE.md`.

## Code quality

Hard limits: 300 lines per file, 100 characters per line, 20 code lines per function, and a
Purpose/Layer header on every source file. See [CODING_STANDARDS.md](CODING_STANDARDS.md).

```bash
pre-commit install && pre-commit run --all-files   # limits, ruff, mypy --strict, import layers, eslint
pytest engine/tests                                 # engine tests (fake voices, no network)
npm --prefix web run lint                           # eslint + vue-tsc
```

## Voices and model routes

| Voice | Notes |
|---|---|
| Sreymom, Piseth (`edge-tts`) | Microsoft neural voices, natural, need internet; text is sent to Microsoft. For commercial use take the same voices from the official Azure Speech service. |
| MMS-TTS (`facebook/mms-tts-khm`) | Offline, basic quality, CC-BY-NC 4.0 (non-commercial). First run downloads ~140 MB. |
| Cloned voices | A base voice speaks the Khmer; the OpenVoice v2 tone-colour converter (MIT) turns it into the recorded timbre. Clips live in `voices/` (git-ignored). Only clone voices you have permission to use. |

Further routes for a better Khmer voice: Fish Speech + LoRA (a specific voice, Kaggle/Colab GPU),
or training Piper/VITS on DDD-Cambodia (lighter, commercially usable; ~8–12 GB VRAM).

## Licences of what ends up in a video

- Pop backgrounds, stickers and bars: drawn by this project's code (`engine/src/sleng/media/pop`).
- Font: Kantumruy Pro, SIL Open Font License 1.1 (`engine/src/sleng/assets/fonts/OFL.txt`).
- Voices: see the table above.
