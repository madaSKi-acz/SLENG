"""Cloned voices: speak Khmer in the timbre of an uploaded recording.

The Khmer speech comes from a base voice (Sreymom, Piseth or MMS); the OpenVoice v2
tone-colour converter (MIT, myshell-ai/OpenVoice) then swaps its timbre for the cloned
speaker's. Pronunciation and rhythm stay the base voice's. Runs on CPU.

OpenVoice's setup.py pins packages that do not build on Python 3.12, so install it without them
(the converter only needs torch + librosa, already in requirements.txt):

    pip install --no-deps https://github.com/myshell-ai/OpenVoice/archive/refs/heads/main.zip

Clones live in voices/<id>/ (ref.wav, se.pt, meta.json); git ignores that folder.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

import numpy as np
import scipy.io.wavfile as wavfile

from render_video import find_ffmpeg
from tts_engine import Engine, polish

VOICE_DIR = Path(__file__).parent.parent / "voices"
REPO = "myshell-ai/OpenVoiceV2"
OPENVOICE_URL = "https://github.com/myshell-ai/OpenVoice/archive/refs/heads/main.zip"
RATE = 22050  # converter sampling rate (converter/config.json)
BASE_FOR = {"woman": "km-KH-SreymomNeural", "man": "km-KH-PisethNeural"}
MIN_SECONDS, MAX_SECONDS = 5, 120
# read once by each base voice to measure its own timbre (the "from" side of the conversion)
BASE_SENTENCES = ["សួស្តី! ខ្ញុំជាសំឡេងភាសាខ្មែរ។", "ថ្ងៃនេះអាកាសធាតុល្អណាស់។",
                  "សូមអរគុណច្រើនសម្រាប់ជំនួយរបស់អ្នក។", "ព្រះរាជាណាចក្រកម្ពុជា ជាប្រទេសមួយនៅអាស៊ីអាគ្នេយ៍។",
                  "តើអ្នកសុខសប្បាយជាទេ?", "ខ្ញុំចូលចិត្តញ៉ាំបាយជាមួយគ្រួសារ។",
                  "ភ្នំពេញ គឺជារាជធានីនៃប្រទេសកម្ពុជា។", "សូមស្វាគមន៍មកកាន់កម្មវិធីរបស់យើង។"]


def decode(data: bytes, rate: int = RATE) -> np.ndarray:
    """Any audio file (wav, mp3, m4a, the browser recorder's webm/ogg...) -> mono float32 at `rate`."""
    ff = find_ffmpeg()
    if not ff:
        raise RuntimeError(f"ffmpeg not found. Install it with: {sys.executable} -m pip install imageio-ffmpeg")
    with tempfile.TemporaryDirectory() as tmp:  # a file, not a pipe: m4a/mp4 need a seekable input
        src = Path(tmp) / "clip"
        src.write_bytes(data)
        p = subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-i", str(src), "-ac", "1", "-ar", str(rate),
                            "-f", "f32le", "pipe:1"], capture_output=True)
    if p.returncode or not p.stdout:
        raise ValueError("Could not read that audio file. " + p.stderr.decode(errors="replace").strip()[-200:])
    return np.frombuffer(p.stdout, dtype=np.float32).copy()


def voiced(wav: np.ndarray) -> np.ndarray:
    """Only the parts with speech (silences dropped)."""
    import librosa

    iv = librosa.effects.split(wav, top_db=35)
    return np.concatenate([wav[a:b] for a, b in iv]) if len(iv) else wav


def to_float(pcm: np.ndarray, rate: int) -> np.ndarray:
    """int16 samples at `rate` -> float32 at the converter's rate."""
    import librosa

    x = pcm.astype(np.float32) / 32768
    return x if rate == RATE else librosa.resample(x, orig_sr=rate, target_sr=RATE)


class Converter:
    """OpenVoice v2 tone-colour converter (lazy load; first use downloads ~130 MB)."""

    def __init__(self, device=None):
        self.device = device
        self._model = self.hps = None
        self._lock = threading.Lock()

    def _load(self):
        if self._model is not None:
            return
        import torch
        from huggingface_hub import hf_hub_download

        try:  # only these modules: openvoice.api pulls in the text front-ends and their old pins
            from openvoice import utils
            from openvoice.models import SynthesizerTrn
        except ImportError as e:
            raise RuntimeError("Voice cloning needs OpenVoice. Install it with the same Python that runs the app: "
                               f"{sys.executable} -m pip install --no-deps {OPENVOICE_URL}") from e

        self.device = self.device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Loading OpenVoice v2 converter on {self.device} (first run downloads ~130 MB)...", flush=True)
        hps = utils.get_hparams_from_file(hf_hub_download(REPO, "converter/config.json"))
        model = SynthesizerTrn(len(getattr(hps, "symbols", [])), hps.data.filter_length // 2 + 1,
                               n_speakers=hps.data.n_speakers, **hps.model).to(self.device).eval()
        ckpt = hf_hub_download(REPO, "converter/checkpoint.pth")
        try:
            state = torch.load(ckpt, map_location=self.device, weights_only=True)
        except Exception:  # checkpoint holds more than tensors
            state = torch.load(ckpt, map_location=self.device, weights_only=False)
        model.load_state_dict(state["model"], strict=False)
        self.hps, self._model = hps, model
        print("Converter ready.", flush=True)

    def _spec(self, wav):
        import torch
        from openvoice.mel_processing import spectrogram_torch

        d = self.hps.data
        y = torch.from_numpy(np.ascontiguousarray(wav, dtype=np.float32)).to(self.device).unsqueeze(0)
        return spectrogram_torch(y, d.filter_length, d.sampling_rate, d.hop_length, d.win_length, center=False)

    def embed(self, wav: np.ndarray):
        """Speaker embedding of float audio at RATE: speech only, averaged over ~10 s pieces."""
        import torch

        x = voiced(wav)
        step = 10 * RATE
        pieces = [x[i:i + step] for i in range(0, len(x), step) if len(x) - i > RATE] or [x]
        with self._lock:
            self._load()
            with torch.no_grad():
                gs = [self._model.ref_enc(self._spec(p).transpose(1, 2)).unsqueeze(-1) for p in pieces]
        return torch.stack(gs).mean(0).cpu()

    def convert(self, wav: np.ndarray, src_se, tgt_se, tau: float = 0.3) -> np.ndarray:
        """Float audio at RATE spoken by `src_se` -> the same speech in the `tgt_se` timbre."""
        import torch

        with self._lock:
            self._load()
            with torch.no_grad():
                spec = self._spec(wav)
                lengths = torch.LongTensor([spec.size(-1)]).to(self.device)
                out = self._model.voice_conversion(spec, lengths, sid_src=src_se.to(self.device),
                                                   sid_tgt=tgt_se.to(self.device), tau=tau)[0]
        return out[0, 0].cpu().float().numpy()


def list_clones() -> dict:
    """{voice id: meta} for every saved clone, oldest first."""
    out = []
    if VOICE_DIR.is_dir():
        for d in VOICE_DIR.iterdir():
            m = d / "meta.json"
            if not d.name.startswith("_") and m.is_file() and (d / "se.pt").is_file():
                out.append(("clone:" + d.name, json.loads(m.read_text("utf-8"))))
    return dict(sorted(out, key=lambda kv: kv[1].get("created", 0)))


def clone_label(meta: dict) -> str:
    return f"{meta['name']} · {meta['gender']} (cloned)"


def clone_dir(vid: str) -> Path:
    m = re.fullmatch(r"clone:([0-9a-f]{10})", str(vid))
    if not m:
        raise ValueError("Unknown voice.")
    return VOICE_DIR / m.group(1)


def add_clone(converter: Converter, name: str, gender: str, base: str, data: bytes):
    """Save a new cloned voice from an audio clip. Returns (voice id, meta)."""
    import torch

    name = " ".join(str(name).split())[:40]
    if not name:
        raise ValueError("Give the voice a name.")
    if gender not in BASE_FOR:
        raise ValueError("Pick woman or man.")
    wav = decode(data)[:MAX_SECONDS * RATE]
    secs = len(voiced(wav)) / RATE
    if secs < MIN_SECONDS:
        raise ValueError(f"Only {secs:.1f} s of speech found. Use at least {MIN_SECONDS} s (10-30 s works best).")
    se = converter.embed(wav)
    vid = uuid.uuid4().hex[:10]
    d = VOICE_DIR / vid
    d.mkdir(parents=True)
    wavfile.write(d / "ref.wav", RATE, (np.clip(wav, -1, 1) * 32767).astype(np.int16))
    torch.save(se, d / "se.pt")
    meta = {"name": name, "gender": gender, "base": base, "seconds": round(secs, 1), "created": time.time()}
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), "utf-8")
    return "clone:" + vid, meta


def delete_clone(vid: str):
    d = clone_dir(vid)
    if d.is_dir():
        shutil.rmtree(d)


class CloneEngine(Engine):
    """Speaks each chunk with the base voice, then converts it to the cloned timbre."""

    def __init__(self, vid: str, base: Engine, base_id: str, converter: Converter):
        import torch

        super().__init__()
        self.base, self.base_id, self.conv = base, base_id, converter
        self.tgt = torch.load(clone_dir(vid) / "se.pt")
        self.rate = RATE
        self._src = None

    def _base_se(self):
        """Timbre of the base voice, measured once and cached in voices/_base/."""
        import torch

        path = VOICE_DIR / "_base" / f"{self.base_id}.pt"
        if path.is_file():
            return torch.load(path)
        pcm = np.concatenate([self.base.synth(s) for s in BASE_SENTENCES])
        se = self.conv.embed(to_float(pcm, self.base.rate))
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(se, path)
        return se

    def synth(self, text: str, speed: float = 1.0) -> np.ndarray:
        key = (text, round(speed, 2))
        with self._lock:
            if key in self._cache:
                return self._cache[key]
            if self._src is None:
                self._src = self._base_se()
            wav = to_float(self.base.synth(text, speed), self.base.rate)
            if len(wav) > RATE // 10:  # too short to convert (e.g. an empty line): keep the base audio
                wav = self.conv.convert(wav, self._src, self.tgt)
            pcm = polish((np.clip(wav, -1, 1) * 32767).astype(np.int16), RATE)
            if len(self._cache) > 500:
                self._cache.clear()
            self._cache[key] = pcm
            return pcm
