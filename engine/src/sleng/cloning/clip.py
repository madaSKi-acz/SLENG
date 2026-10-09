"""
Purpose:  Read an uploaded or recorded clip (any format) as mono float audio for the converter.
Layer:    sleng.cloning
Exports:  CONVERTER_RATE, MIN_SPEECH_SECONDS, MAX_CLIP_SECONDS, decode_clip, voiced, speech_seconds
Depends:  sleng.infra.ffmpeg, sleng.audio.cleanup (CLIP_CHAIN), librosa (lazy)
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np

from sleng.audio.cleanup import CLIP_CHAIN
from sleng.domain.audio import FloatSamples
from sleng.domain.errors import InvalidInputError
from sleng.infra.deps import require
from sleng.infra.ffmpeg import Ffmpeg, FfmpegError

CONVERTER_RATE = 22050  # OpenVoice v2 converter sampling rate (converter/config.json)
MIN_SPEECH_SECONDS = 5
MAX_CLIP_SECONDS = 120
SILENCE_TOP_DB = 35


def decode_clip(data: bytes, ffmpeg: Ffmpeg, clean: bool) -> FloatSamples:
    """wav/mp3/m4a/webm/ogg... -> mono float32 at CONVERTER_RATE, at most MAX_CLIP_SECONDS.

    clean=True also removes rumble, hum and steady noise, then evens out the peak level.
    """
    if not data:
        raise InvalidInputError("Upload or record a clip first.")
    with tempfile.TemporaryDirectory() as tmp:  # a file, not a pipe: m4a/mp4 need seeking
        source = Path(tmp) / "clip"
        source.write_bytes(data)
        raw = _run_decoder(ffmpeg, source, clean)
    limit = MAX_CLIP_SECONDS * CONVERTER_RATE
    wave: FloatSamples = np.frombuffer(raw, dtype=np.float32)[:limit].copy()
    peak = float(np.abs(wave).max()) if wave.size else 0.0
    if clean and peak > 1e-4:
        wave = (wave * (0.9 / peak)).astype(np.float32)
    return wave


def voiced(wave: FloatSamples) -> FloatSamples:
    """Only the parts with speech (silences dropped)."""
    librosa = require("librosa")
    intervals = librosa.effects.split(wave, top_db=SILENCE_TOP_DB)
    if not len(intervals):
        return wave
    return np.concatenate([wave[start:end] for start, end in intervals])


def speech_seconds(wave: FloatSamples) -> float:
    """Seconds of actual speech in a clip at CONVERTER_RATE."""
    return len(voiced(wave)) / CONVERTER_RATE


def _run_decoder(ffmpeg: Ffmpeg, source: Path, clean: bool) -> bytes:
    filters = ["-af", CLIP_CHAIN] if clean else []
    rate = str(CONVERTER_RATE)
    args = ["-i", str(source), *filters, "-ac", "1", "-ar", rate, "-f", "f32le", "pipe:1"]
    try:
        return ffmpeg.pipe(args)
    except FfmpegError as err:
        raise InvalidInputError(f"Could not read that audio file. {err}") from err
