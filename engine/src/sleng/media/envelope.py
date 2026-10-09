"""
Purpose:  Loudness envelope of the narration (0..1 every 10 ms) that drives the voice bars.
Layer:    sleng.media
Exports:  loudness_envelope, ENVELOPE_STEP
Depends:  numpy, sleng.domain.audio
"""

from __future__ import annotations

import numpy as np

from sleng.domain.audio import Audio, FloatSamples

ENVELOPE_STEP = 0.01  # seconds per envelope value
RELEASE = 0.88  # how slowly the bars fall back (fast attack, slow release)


def loudness_envelope(audio: Audio, step: float = ENVELOPE_STEP) -> FloatSamples:
    """RMS per `step`, normalised to the 95th percentile and gently compressed."""
    wave = audio.samples.astype(np.float32)
    hop = max(1, int(audio.rate * step))
    frames = len(wave) // hop
    if frames == 0:
        return np.zeros(1, dtype=np.float32)
    rms = np.sqrt((wave[: frames * hop].reshape(frames, hop) ** 2).mean(axis=1))
    voiced = rms[rms > 0]
    reference = float(np.percentile(voiced, 95)) if voiced.size else 1.0
    level = np.clip(rms / max(reference, 1e-6), 0, 1) ** 0.6
    return _attack_release(level.astype(np.float32))


def _attack_release(level: FloatSamples) -> FloatSamples:
    out = np.empty_like(level)
    value = 0.0
    for index, target in enumerate(level.tolist()):
        value = target if target > value else value * RELEASE + target * (1 - RELEASE)
        out[index] = value
    return out
