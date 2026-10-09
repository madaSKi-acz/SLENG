"""
Purpose:  Convert Audio to float samples at another sample rate (for the voice converter).
Layer:    sleng.audio
Exports:  to_float_at
Depends:  sleng.domain.audio, librosa (lazy, only when the rates differ)
"""

from __future__ import annotations

import numpy as np

from sleng.domain.audio import Audio, FloatSamples
from sleng.infra.deps import require


def to_float_at(audio: Audio, rate: int) -> FloatSamples:
    """Float32 samples in [-1, 1) at `rate`."""
    wave = audio.to_float()
    if audio.rate == rate:
        return wave
    librosa = require("librosa")
    resampled = librosa.resample(wave, orig_sr=audio.rate, target_sr=rate)
    return np.asarray(resampled, dtype=np.float32)
