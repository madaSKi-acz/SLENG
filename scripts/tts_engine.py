"""Shared MMS-TTS engine: lazy model load, per-chunk synthesis, WAV encoding."""
import io
import threading

import numpy as np
import scipy.io.wavfile as wavfile

MODEL_ID = "facebook/mms-tts-khm"


def polish(pcm: np.ndarray, rate: int, pad_ms: int = 40, fade_ms: int = 12) -> np.ndarray:
    """Trim leading/trailing silence (keep a small pad) and fade the edges to avoid clicks."""
    if pcm.size < 2:
        return pcm
    x = pcm.astype(np.float32)
    thr = max(0.01 * np.abs(x).max(), 30.0)
    idx = np.flatnonzero(np.abs(x) > thr)
    if idx.size:
        pad = int(rate * pad_ms / 1000)
        x = x[max(idx[0] - pad, 0): idx[-1] + pad + 1]
    n = min(int(rate * fade_ms / 1000), len(x) // 2)
    if n > 1:
        ramp = np.linspace(0, 1, n, dtype=np.float32)
        x[:n] *= ramp
        x[-n:] *= ramp[::-1]
    return x.astype(np.int16)


class Engine:
    def __init__(self, device=None, fake=False):
        self.fake = fake
        self.device = device
        self.rate = 16000
        self._lock = threading.Lock()
        self._model = self._tok = None
        self._cache = {}

    def _load(self):
        if self._model is not None or self.fake:
            return
        import torch
        from transformers import AutoTokenizer, VitsModel

        self.device = self.device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Loading {MODEL_ID} on {self.device} (first run downloads ~140 MB)...", flush=True)
        self._tok = AutoTokenizer.from_pretrained(MODEL_ID)
        self._model = VitsModel.from_pretrained(MODEL_ID).to(self.device).eval()
        self.rate = self._model.config.sampling_rate
        print("Model ready.", flush=True)

    def synth(self, text: str, speed: float = 1.0) -> np.ndarray:
        """Return int16 samples for one chunk of text (cached)."""
        key = (text, round(speed, 2))
        with self._lock:
            if key in self._cache:
                return self._cache[key]
            self._load()
            if self.fake:  # test mode: tone whose length follows text length
                t = np.linspace(0, 0.04 * len(text), int(self.rate * 0.04 * len(text)), endpoint=False)
                wav = (0.2 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
            else:
                import torch

                self._model.speaking_rate = speed
                inputs = self._tok(text, return_tensors="pt").to(self.device)
                if inputs["input_ids"].numel() == 0:
                    wav = np.zeros(1, dtype=np.float32)
                else:
                    with torch.no_grad():
                        wav = self._model(**inputs).waveform[0].cpu().numpy()
            pcm = polish((np.clip(wav, -1, 1) * 32767).astype(np.int16), self.rate)
            if len(self._cache) > 500:
                self._cache.clear()
            self._cache[key] = pcm
            return pcm

    def to_wav(self, pcm: np.ndarray) -> bytes:
        buf = io.BytesIO()
        wavfile.write(buf, self.rate, pcm)
        return buf.getvalue()

    def silence(self, seconds: float) -> np.ndarray:
        return np.zeros(int(seconds * self.rate), dtype=np.int16)


class EdgeEngine(Engine):
    """Microsoft neural Khmer voices via the `edge-tts` package (needs internet).

    Voices: km-KH-SreymomNeural (female), km-KH-PisethNeural (male).
    Much more natural than MMS-TTS, but it is an online service: text is sent
    to Microsoft, and edge-tts is unofficial (for commercial use, use the
    official Azure Speech service, which has the same voices).
    """

    def __init__(self, voice="km-KH-SreymomNeural"):
        super().__init__(fake=False)
        self.voice = voice
        self.rate = 24000

    def synth(self, text: str, speed: float = 1.0) -> np.ndarray:
        key = (text, round(speed, 2))
        with self._lock:
            if key in self._cache:
                return self._cache[key]
            import asyncio

            import edge_tts
            import soundfile as sf

            async def fetch():
                rate = f"{round((speed - 1) * 100):+d}%"
                data = b""
                async for part in edge_tts.Communicate(text, self.voice, rate=rate).stream():
                    if part["type"] == "audio":
                        data += part["data"]
                return data

            mp3 = asyncio.run(fetch())
            if not mp3:
                raise RuntimeError("Edge TTS returned no audio (offline, or the service blocked the request)")
            pcm, sr = sf.read(io.BytesIO(mp3), dtype="int16")
            if pcm.ndim > 1:
                pcm = pcm[:, 0]
            self.rate = sr
            pcm = polish(pcm, sr)
            if len(self._cache) > 500:
                self._cache.clear()
            self._cache[key] = pcm
            return pcm
