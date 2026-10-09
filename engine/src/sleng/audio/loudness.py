"""
Purpose:  Loudness helpers: even out the level of a chunk, and keep peaks under a ceiling.
Layer:    sleng.audio
Exports:  match_level, peak_limit
Depends:  numpy
"""

from __future__ import annotations

import numpy as np

from sleng.domain.audio import FloatSamples

TARGET_RMS = 3000.0  # int16 units, measured on the active (non-silent) part
MIN_GAIN, MAX_GAIN = 0.4, 2.5
PEAK_CEILING = 30000.0


def match_level(wave: FloatSamples) -> FloatSamples:
    """Scale a chunk (int16-range floats) towards TARGET_RMS without exceeding PEAK_CEILING."""
    if not wave.size:
        return wave
    peak = float(np.abs(wave).max())
    active = wave[np.abs(wave) > 0.02 * max(peak, 1.0)]
    rms = float(np.sqrt(np.mean(active**2))) if active.size else 0.0
    if rms > 0:
        wave = wave * float(np.clip(TARGET_RMS / rms, MIN_GAIN, MAX_GAIN))
    peak = float(np.abs(wave).max())
    return wave * (PEAK_CEILING / peak) if peak > PEAK_CEILING else wave


def peak_limit(wave: FloatSamples, peak: float = 0.97) -> FloatSamples:
    """Float audio in [-1, 1]: scale down only if the loudest sample is above `peak`."""
    loudest = float(np.abs(wave).max()) if wave.size else 0.0
    return wave * (peak / loudest) if loudest > peak else wave
