"""Local web UI for Khmer TTS (facebook/mms-tts-khm).

    python scripts/app.py              # then open http://127.0.0.1:7860
    python scripts/app.py --port 8000 --device cpu

Only the standard library plus the packages in requirements.txt are needed.
"""
import argparse
import base64
import io
import json
import random
import sys
import tempfile
import threading
import webbrowser
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from audio_fx import clean_voice  # noqa: E402
from khmer_text import normalize, split_chunks_ex  # noqa: E402
from render_video import ACCENTS, FONT_DIR, find_fonts, render_mp4  # noqa: E402
from subtitles import make_cues, to_ass, to_srt  # noqa: E402
from tts_engine import EdgeEngine, Engine, merge_timeline  # noqa: E402
from voice_clone import (BASE_FOR, CloneEngine, Converter, add_clone, clone_label, delete_clone,  # noqa: E402
                         list_clones, preview_wav)

HTML = (Path(__file__).parent / "ui.html").read_bytes()
engines = {}  # voice id -> engine, created on first use
fx_cache = {}  # (engine, text, speed, cleanup level) -> cleaned samples
VOICES = {"km-KH-SreymomNeural": "Sreymom · female (online, natural)",
          "km-KH-PisethNeural": "Piseth · male (online, natural)",
          "mms": "MMS-TTS (offline, basic)"}
CONFIG = {"device": None, "fake": False, "font": None, "font_name": None}
converter = Converter()  # shared by every cloned voice


def get_engine(voice):
    if voice not in engines:
        meta = list_clones().get(voice)
        if meta:
            engines[voice] = CloneEngine(voice, get_engine(meta["base"]), meta["base"], converter)
        elif voice in VOICES:
            engines[voice] = Engine(device=CONFIG["device"], fake=CONFIG["fake"]) if voice == "mms" else EdgeEngine(voice)
        else:
            return get_engine("mms")
    return engines[voice]


VOICE_CARDS = {"km-KH-SreymomNeural": ("Sreymom", "Woman, online"), "km-KH-PisethNeural": ("Piseth", "Man, online"),
               "mms": ("MMS", "Offline, basic")}  # name and note on the UI's voice cards


def voice_list():
    out = [{"id": k, "label": v, "group": "Built-in voices", "base": k, "name": VOICE_CARDS[k][0], "note": VOICE_CARDS[k][1]}
           for k, v in VOICES.items()]
    out += [{"id": k, "label": clone_label(m), "group": "Cloned voices", "base": m["base"], "clone": True,
             "name": m["name"], "note": m["gender"].capitalize() + ", cloned"} for k, m in list_clones().items()]
    return out


def get_chunks(req):
    """Chunks to synthesize: the client's (possibly edited) list, else split the text."""
    if req.get("chunks"):
        out = []
        for c in req["chunks"]:
            display = str(c.get("text", "")).strip()
            speak = normalize(display)
            if speak:
                out.append({"display": display, "speak": speak, "kind": c.get("kind", "sentence")})
        return out
    return split_chunks_ex(req.get("text", ""), int(req.get("max_chars", 110)))


def speak_chunk(engine, text, speed, fx):
    """One chunk of speech, with the voice cleanup level from the UI applied (off / light / studio)."""
    pcm = engine.synth(text, speed)
    if fx not in ("light", "studio"):
        return pcm
    key = (id(engine), text, round(speed, 2), fx)
    if key not in fx_cache:
        if len(fx_cache) > 500:
            fx_cache.clear()
        fx_cache[key] = clean_voice(pcm, engine.rate, fx)
    return fx_cache[key]


def build(req, engine):
    """Synthesize all chunks and join them. Returns (pcm, chunks, spans)."""
    chunks = get_chunks(req)
    if not chunks:
        raise ValueError("No readable text.")
    speed = float(req.get("speed", 1.0))
    fx = req.get("fx", "light")
    parts = [(speak_chunk(engine, c["speak"], speed, fx), c["kind"]) for c in chunks]
    pcm, spans = merge_timeline(parts, engine.rate, float(req.get("pause", 0.2)), float(req.get("para_pause", 0.6)),
                                smart=bool(req.get("smart", True)))
    return pcm, chunks, spans


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *a):  # quieter console
        pass

    def _send(self, code, body, ctype, headers=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, HTML, "text/html; charset=utf-8")
        elif self.path.startswith("/fonts/") and Path(self.path).name in {f.name for f in FONT_DIR.glob("*.ttf")}:
            self._send(200, (FONT_DIR / Path(self.path).name).read_bytes(), "font/ttf")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n) or b"{}")
            engine = get_engine(req.get("voice", "mms"))
            if self.path == "/api/voices":
                self._json(voice_list())
            elif self.path == "/api/voice/add":
                gender = req.get("gender", "")
                base = req.get("base") if req.get("base") in VOICES else BASE_FOR.get(gender, "mms")
                audio = base64.b64decode(req.get("audio") or "")
                if not audio:
                    return self._json({"error": "Upload or record a clip first."}, 400)
                vid, meta = add_clone(converter, req.get("name", ""), gender, base, audio, bool(req.get("clean", True)))
                self._json({"id": vid, "label": clone_label(meta)})
            elif self.path == "/api/voice/preview":
                audio = base64.b64decode(req.get("audio") or "")
                if not audio:
                    return self._json({"error": "Upload or record a clip first."}, 400)
                self._send(200, preview_wav(audio, bool(req.get("clean", True))), "audio/wav")
            elif self.path == "/api/voice/delete":
                delete_clone(req.get("id", ""))
                engines.pop(req.get("id", ""), None)
                self._json({"ok": True})
            elif self.path == "/api/split":
                chunks = split_chunks_ex(req.get("text", ""), int(req.get("max_chars", 110)))
                self._json([{"text": c["display"], "pause": c["kind"]} for c in chunks])
            elif self.path == "/api/synth":
                speak = normalize(req["text"])
                if not speak:
                    return self._json({"error": "This line has no readable text."}, 400)
                pcm = speak_chunk(engine, speak, float(req.get("speed", 1.0)), req.get("fx", "light"))
                self._send(200, engine.to_wav(pcm), "audio/wav")
            elif self.path == "/api/full":
                pcm, _, _ = build(req, engine)
                self._send(200, engine.to_wav(pcm), "audio/wav")
            elif self.path == "/api/zip":
                chunks = get_chunks(req)
                if not chunks:
                    return self._json({"error": "No readable text."}, 400)
                speed = float(req.get("speed", 1.0))
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
                    for i, c in enumerate(chunks, 1):
                        pcm = speak_chunk(engine, c["speak"], speed, req.get("fx", "light"))
                        z.writestr(f"{i:03d}.wav", engine.to_wav(pcm))
                    z.writestr("chunks.txt", "\n".join(f"{i:03d}\t{c['display']}" for i, c in enumerate(chunks, 1)))
                self._send(200, buf.getvalue(), "application/zip")
            elif self.path == "/api/srt":
                pcm, chunks, spans = build(req, engine)
                cues = make_cues([c["display"] for c in chunks], spans)
                self._send(200, to_srt(cues).encode("utf-8"), "text/plain; charset=utf-8")
            elif self.path == "/api/render":
                pcm, chunks, spans = build(req, engine)
                w, h = int(req.get("width", 1280)), int(req.get("height", 720))
                title = str(req.get("title", "")).strip()
                intro = float(req.get("intro", 2.6)) if title else 0.0
                if intro:  # title card first: pad the audio and push every subtitle later
                    pcm = np.concatenate([np.zeros(int(intro * engine.rate), dtype=np.int16), pcm])
                    spans = [(a + intro, b + intro) for a, b in spans]
                dur = len(pcm) / engine.rate
                fonts, family = find_fonts(CONFIG["font"], CONFIG["font_name"])
                ass = None
                theme = req.get("theme", "studio")
                seed = int(req.get("seed") or random.randint(1, 99999))
                pop = theme == "pop"
                if req.get("burn", True):
                    cues = make_cues([c["display"] for c in chunks], spans, int(req.get("sub_chars", 60)))
                    ass = to_ass(cues, w, h, family, int(min(w, h) * float(req.get("font_scale", 0.075))),
                                 accent=ACCENTS.get(req.get("accent", "gemini"), ACCENTS["gemini"]),
                                 karaoke=bool(req.get("karaoke", True)), title=title, duration=dur, intro=intro,
                                 **(dict(hi=(255, 226, 60), dim=(255, 255, 255), card=(255, 255, 255), bold_outline=True) if pop else {}))
                with tempfile.TemporaryDirectory() as tmp:
                    out = Path(tmp) / "video.mp4"
                    render_mp4(engine.to_wav(pcm), ass, w, h, dur, fonts, str(out), theme=theme,
                               accent=req.get("accent", "gemini"), progress=bool(req.get("progress", True)), seed=seed)
                    self._send(200, out.read_bytes(), "video/mp4", {"X-Seed": str(seed)})
            else:
                self._send(404, b"not found", "text/plain")
        except Exception as e:  # report to the UI instead of dropping the connection
            print("error:", repr(e), flush=True)
            self._json({"error": str(e)}, 400 if isinstance(e, ValueError) else 500)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=7860)
    p.add_argument("--device", default=None, help="cpu or cuda (default: auto)")
    p.add_argument("--font", help="Use this .ttf/.otf for subtitles instead of the bundled Kantumruy Pro")
    p.add_argument("--font-name", help="Font family name if it cannot be read from the file")
    p.add_argument("--no-browser", action="store_true")
    p.add_argument("--fake", action="store_true", help="test mode: tones instead of the model")
    args = p.parse_args()

    CONFIG.update(device=args.device, fake=args.fake, font=args.font, font_name=args.font_name)
    converter.device = args.device
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}"
    print(f"Khmer TTS UI running at {url}  (Ctrl+C to stop)", flush=True)
    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    if not args.fake:  # warm up the offline model in the background
        threading.Thread(target=lambda: get_engine("mms").synth("ក", 1.0), daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
