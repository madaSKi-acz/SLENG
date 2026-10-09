"""
Purpose:  Clean generated speech with ffmpeg filter chains (light / studio); "off" leaves it alone.
Layer:    sleng.audio
Exports:  VoiceCleaner, CHAINS, CLIP_CHAIN
Depends:  sleng.infra.ffmpeg, sleng.audio.loudness, sleng.domain
Notes:    Output is read back as float and peak-limited in numpy, so a loud filter never hard-clips
          (alimiter is avoided: its latency option differs between ffmpeg versions).
"""

from __future__ import annotations

import numpy as np

from sleng.audio.loudness import peak_limit
from sleng.domain.audio import Audio
from sleng.domain.options import CleanupLevel
from sleng.infra.ffmpeg import Ffmpeg, FfmpegError

# Cleans a recording before it is cloned: rumble, hum, steady room noise and hiss.
CLIP_CHAIN = "highpass=f=90,lowpass=f=10000,afftdn=nr=20:nf=-30:tn=1"
CHAINS: dict[CleanupLevel, str] = {
    # rumble cut + gentle noise reduction (takes the hiss off cloned voices)
    CleanupLevel.LIGHT: "highpass=f=70,afftdn=nr=8:nf=-45:tn=1",
    # light + stronger denoise, less boom, more presence, softer "s", even volume
    CleanupLevel.STUDIO: (
        "highpass=f=80,afftdn=nr=14:nf=-40:tn=1,"
        "equalizer=f=250:t=q:w=1:g=-2,equalizer=f=3500:t=q:w=1:g=2.5,"
        "deesser=i=0.4,acompressor=threshold=0.1:ratio=3:attack=5:release=120:makeup=1.6"
    ),
}


class VoiceCleaner:
    """Runs speech through the filter chain for a cleanup level."""

    def __init__(self, ffmpeg: Ffmpeg) -> None:
        self._ffmpeg = ffmpeg

    def clean(self, audio: Audio, level: CleanupLevel) -> Audio:
        """Same rate and (about) the same length back; too-short audio is returned unchanged."""
        chain = CHAINS.get(level)
        if chain is None or len(audio.samples) < audio.rate // 20:
            return audio
        data = audio.samples.astype("<i2").tobytes()
        try:
            raw = self._ffmpeg.pipe(_filter_args(audio.rate, chain), data)
        except FfmpegError as err:
            raise FfmpegError(f"Voice cleanup failed: {err}") from err
        wave = peak_limit(np.frombuffer(raw, dtype="<f4").astype(np.float32))
        return Audio.from_float(wave, audio.rate)


def _filter_args(rate: int, chain: str) -> list[str]:
    hz = str(rate)
    source = ["-f", "s16le", "-ar", hz, "-ac", "1", "-i", "pipe:0"]
    return [*source, "-af", chain, "-f", "f32le", "-ar", hz, "-ac", "1", "pipe:1"]
