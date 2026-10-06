"""Local web UI for Khmer TTS (facebook/mms-tts-khm).

    python scripts/app.py              # then open http://127.0.0.1:7860
    python scripts/app.py --port 8000 --device cpu

Only the standard library plus the packages in requirements.txt are needed.
"""
import argparse
import io
import json
import sys
import tempfile
import threading
import webbrowser
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from khmer_text import normalize, split_chunks_ex  # noqa: E402
from render_video import find_font, render_mp4  # noqa: E402
from subtitles import make_cues, to_ass, to_srt  # noqa: E402
from tts_engine import EdgeEngine, Engine, merge_timeline  # noqa: E402

HTML = (Path(__file__).parent / "ui.html").read_bytes()
engines = {}  # voice id -> engine, created on first use
VOICES = {"mms": "MMS-TTS (offline, basic)",
          "km-KH-SreymomNeural": "Sreymom · female (online, natural)",
          "km-KH-PisethNeural": "Piseth · male (online, natural)"}
CONFIG = {"device": None, "fake": False, "font": None, "font_name": None}


def get_engine(voice):
    voice = voice if voice in VOICES else "mms"
    if voice not in engines:
        engines[voice] = Engine(device=CONFIG["device"], fake=CONFIG["fake"]) if voice == "mms" else EdgeEngine(voice)
    return engines[voice]


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


def build(req, engine):
    """Synthesize all chunks and join them. Returns (pcm, chunks, spans)."""
    chunks = get_chunks(req)
    if not chunks:
        raise ValueError("No readable text.")
    speed = float(req.get("speed", 1.0))
    parts = [(engine.synth(c["speak"], speed), c["kind"]) for c in chunks]
    pcm, spans = merge_timeline(parts, engine.rate, float(req.get("pause", 0.2)), float(req.get("para_pause", 0.6)),
                                smart=bool(req.get("smart", True)))
    return pcm, chunks, spans


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *a):  # quieter console
        pass

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, HTML, "text/html; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n) or b"{}")
            engine = get_engine(req.get("voice", "mms"))
            if self.path == "/api/voices":
                self._json(VOICES)
            elif self.path == "/api/split":
                chunks = split_chunks_ex(req.get("text", ""), int(req.get("max_chars", 110)))
                self._json([{"text": c["display"], "pause": c["kind"]} for c in chunks])
            elif self.path == "/api/synth":
                speak = normalize(req["text"])
                if not speak:
                    return self._json({"error": "This line has no readable text."}, 400)
                self._send(200, engine.to_wav(engine.synth(speak, float(req.get("speed", 1.0)))), "audio/wav")
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
                        z.writestr(f"{i:03d}.wav", engine.to_wav(engine.synth(c["speak"], speed)))
                    z.writestr("chunks.txt", "\n".join(f"{i:03d}\t{c['display']}" for i, c in enumerate(chunks, 1)))
                self._send(200, buf.getvalue(), "application/zip")
            elif self.path == "/api/srt":
                pcm, chunks, spans = build(req, engine)
                cues = make_cues([c["display"] for c in chunks], spans)
                self._send(200, to_srt(cues).encode("utf-8"), "text/plain; charset=utf-8")
            elif self.path == "/api/render":
                pcm, chunks, spans = build(req, engine)
                w, h = int(req.get("width", 1280)), int(req.get("height", 720))
                ass = None
                if req.get("burn", True):
                    font, family = find_font(CONFIG["font"], CONFIG["font_name"])
                    if not font:
                        raise RuntimeError("No Khmer font found. Start the app with --font C:\\path\\to\\font.ttf "
                                           "(e.g. Leelawadee UI or Noto Sans Khmer).")
                    cues = make_cues([c["display"] for c in chunks], spans, int(req.get("sub_chars", 60)))
                    ass = to_ass(cues, w, h, family, int(min(w, h) * float(req.get("font_scale", 0.075))))
                else:
                    font = None
                with tempfile.TemporaryDirectory() as tmp:
                    out = Path(tmp) / "video.mp4"
                    render_mp4(engine.to_wav(pcm), ass, w, h, len(pcm) / engine.rate, font, str(out))
                    self._send(200, out.read_bytes(), "video/mp4")
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
    p.add_argument("--font", help="Khmer .ttf/.otf used for burned-in subtitles (default: auto-detect)")
    p.add_argument("--font-name", help="Font family name if it cannot be read from the file")
    p.add_argument("--no-browser", action="store_true")
    p.add_argument("--fake", action="store_true", help="test mode: tones instead of the model")
    args = p.parse_args()

    CONFIG.update(device=args.device, fake=args.fake, font=args.font, font_name=args.font_name)
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
