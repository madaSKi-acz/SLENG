"""
Purpose:  Trim leading/trailing silence (keeping a small pad) and fade the edges to avoid clicks.
Layer:    sleng.audio
Exports:  polish
Depends:  sleng.domain.audio, numpy
"""

from __future__ import annotations

import numpy as np

from sleng.domain.audio import Audio, FloatSamples

PAD_MS = 40
FADE_MS = 12
SILENCE_FLOOR = 30.0  # int16 units; quieter than this never counts as speech


def polish(audio: Audio) -> Audio:
    """Every voice engine passes its output through this before returning it."""
    if audio.samples.size < 2:
        return audio
    wave = audio.samples.astype(np.float32)
    wave = _fade(_trim(wave, audio.rate), audio.rate)
    return Audio(wave.astype(np.int16), audio.rate)


def _trim(wave: FloatSamples, rate: int) -> FloatSamples:
    threshold = max(0.01 * float(np.abs(wave).max()), SILENCE_FLOOR)
    loud = np.flatnonzero(np.abs(wave) > threshold)
    if not loud.size:
        return wave
    pad = int(rate * PAD_MS / 1000)
    return wave[max(int(loud[0]) - pad, 0) : int(loud[-1]) + pad + 1]


def _fade(wave: FloatSamples, rate: int) -> FloatSamples:
    length = min(int(rate * FADE_MS / 1000), len(wave) // 2)
    if length > 1:
        ramp = np.linspace(0, 1, length, dtype=np.float32)
        wave[:length] *= ramp
        wave[-length:] *= ramp[::-1]
    return wave
