"""
Purpose:  Encode Audio as WAV bytes (16-bit PCM, mono).
Layer:    sleng.audio
Exports:  encode_wav
Depends:  sleng.domain.audio, scipy
"""

from __future__ import annotations

import io

import numpy as np
from scipy.io import wavfile

from sleng.domain.audio import Audio


def encode_wav(audio: Audio) -> bytes:
    """WAV file content for `audio`."""
    buffer = io.BytesIO()
    wavfile.write(buffer, audio.rate, np.asarray(audio.samples))
    return buffer.getvalue()
