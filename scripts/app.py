"""Local web UI for Khmer TTS (facebook/mms-tts-khm).

    python scripts/app.py              # then open http://127.0.0.1:7860
    python scripts/app.py --port 8000 --device cpu

Only the standard library plus the packages in requirements.txt are needed.
"""
import argparse
import json
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from khmer_text import split_chunks  # noqa: E402
from tts_engine import EdgeEngine, Engine  # noqa: E402

HTML = (Path(__file__).parent / "ui.html").read_bytes()
engines = {}  # voice id -> engine, created on first use
VOICES = {"mms": "MMS-TTS (offline, basic)",
          "km-KH-SreymomNeural": "Sreymom · female (online, natural)",
          "km-KH-PisethNeural": "Piseth · male (online, natural)"}
CONFIG = {"device": None, "fake": False}


def get_engine(voice):
    voice = voice if voice in VOICES else "mms"
    if voice not in engines:
        engines[voice] = Engine(device=CONFIG["device"], fake=CONFIG["fake"]) if voice == "mms" else EdgeEngine(voice)
    return engines[voice]


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
                chunks = split_chunks(req.get("text", ""), int(req.get("max_chars", 110)))
                self._json([{"text": t, "pause": k} for t, k in chunks])
            elif self.path == "/api/synth":
                pcm = engine.synth(req["text"], float(req.get("speed", 1.0)))
                self._send(200, engine.to_wav(pcm), "audio/wav")
            elif self.path == "/api/full":
                speed = float(req.get("speed", 1.0))
                pause, para = float(req.get("pause", 0.35)), float(req.get("para_pause", 0.8))
                parts = []
                for text, kind in split_chunks(req.get("text", ""), int(req.get("max_chars", 110))):
                    parts += [engine.synth(text, speed), engine.silence(para if kind == "paragraph" else pause)]
                if not parts:
                    return self._json({"error": "no text"}, 400)
                self._send(200, engine.to_wav(np.concatenate(parts)), "audio/wav")
            else:
                self._send(404, b"not found", "text/plain")
        except Exception as e:  # report to the UI instead of dropping the connection
            print("error:", repr(e), flush=True)
            self._json({"error": str(e)}, 500)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=7860)
    p.add_argument("--device", default=None, help="cpu or cuda (default: auto)")
    p.add_argument("--no-browser", action="store_true")
    p.add_argument("--fake", action="store_true", help="test mode: tones instead of the model")
    args = p.parse_args()

    CONFIG.update(device=args.device, fake=args.fake)
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
