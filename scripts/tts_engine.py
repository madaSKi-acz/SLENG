"""Shared MMS-TTS engine: lazy model load, per-chunk synthesis, WAV encoding."""
import io
import threading

import numpy as np
import scipy.io.wavfile as wavfile

MODEL_ID = "facebook/mms-tts-khm"


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
            pcm = (np.clip(wav, -1, 1) * 32767).astype(np.int16)
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
