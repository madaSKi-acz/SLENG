"""Voice cleanup with ffmpeg filters (the ffmpeg bundled by imageio-ffmpeg, so nothing extra to install).

Two uses:
- CLIP_CHAIN cleans a recording before it is cloned (room noise, hum, rumble, hiss).
- CHAINS clean and polish the generated speech, chunk by chunk:
    light  : rumble cut + gentle noise reduction (takes the hiss off cloned voices)
    studio : light + stronger denoise, less boom, more presence, softer "s", even volume
"""
import sys
import subprocess

import numpy as np

from render_video import find_ffmpeg

CLIP_CHAIN = "highpass=f=90,lowpass=f=10000,afftdn=nr=20:nf=-30:tn=1"
CHAINS = {
    "light": "highpass=f=70,afftdn=nr=8:nf=-45:tn=1",
    "studio": ("highpass=f=80,afftdn=nr=14:nf=-40:tn=1,"
               "equalizer=f=250:t=q:w=1:g=-2,equalizer=f=3500:t=q:w=1:g=2.5,"
               "deesser=i=0.4,acompressor=threshold=0.1:ratio=3:attack=5:release=120:makeup=1.6"),
}


def ffmpeg_exe():
    ff = find_ffmpeg()
    if not ff:
        raise RuntimeError(f"ffmpeg not found. Install it with: {sys.executable} -m pip install imageio-ffmpeg")
    return ff


def peak_limit(x: np.ndarray, peak: float = 0.97) -> np.ndarray:
    m = float(np.abs(x).max()) if x.size else 0.0
    return x * (peak / m) if m > peak else x


def apply(pcm: np.ndarray, rate: int, chain: str) -> np.ndarray:
    """Run int16 mono samples through an ffmpeg filter chain; same rate and length back."""
    if pcm.size < rate // 20:  # too short to filter (e.g. an empty line)
        return pcm
    p = subprocess.run([ffmpeg_exe(), "-hide_banner", "-loglevel", "error",
                        "-f", "s16le", "-ar", str(rate), "-ac", "1", "-i", "pipe:0",
                        "-af", chain, "-f", "f32le", "-ar", str(rate), "-ac", "1", "pipe:1"],
                       input=pcm.astype("<i2").tobytes(), capture_output=True)
    if p.returncode or not p.stdout:
        raise RuntimeError("Voice cleanup failed: " + p.stderr.decode(errors="replace").strip()[-200:])
    x = peak_limit(np.frombuffer(p.stdout, dtype="<f4"))  # float out, so a loud filter never hard-clips
    return (np.clip(x, -1, 1) * 32767).astype(np.int16)


def clean_voice(pcm: np.ndarray, rate: int, level: str) -> np.ndarray:
    """Generated speech -> cleaned speech for level 'light' or 'studio'; anything else returns it unchanged."""
    return apply(pcm, rate, CHAINS[level]) if level in CHAINS else pcm
