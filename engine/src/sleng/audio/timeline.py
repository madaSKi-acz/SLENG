"""
Purpose:  Join synthesized chunks into one narration and record where each chunk sits in it.
Layer:    sleng.audio
Exports:  merge
Depends:  sleng.domain.audio, sleng.domain.errors, sleng.audio.loudness, numpy
Notes:    smart=True evens loudness per chunk and crossfades when the gap is (almost) zero;
          smart=False is a plain join with fixed silences.
"""

from __future__ import annotations

from collections.abc import Sequence
from itertools import pairwise

import numpy as np

from sleng.audio.loudness import match_level
from sleng.domain.audio import Audio, FloatSamples, Timeline
from sleng.domain.errors import InvalidInputError

CROSSFADE_BELOW = 0.03  # seconds: gaps shorter than this become a crossfade
CROSSFADE_LENGTH = 0.02  # seconds
SampleSpan = tuple[int, int]


def merge(parts: Sequence[tuple[Audio, float]], smart: bool = True) -> Timeline:
    """`parts` = (chunk audio, seconds of silence after it). All chunks share one sample rate."""
    if not parts:
        raise InvalidInputError("No readable text.")
    rate = parts[0][0].rate
    waves = [(_prepare(audio, smart), gap) for audio, gap in parts]
    out = waves[0][0]
    spans: list[SampleSpan] = [(0, len(out))]
    for (_, gap), (wave, _) in pairwise(waves):
        out, span = _append(out, wave, int(gap * rate), smart, rate)
        spans.append(span)
    samples = np.clip(out, -32768, 32767).astype(np.int16)
    seconds = tuple((start / rate, end / rate) for start, end in spans)
    return Timeline(Audio(samples, rate), seconds)


def _prepare(audio: Audio, smart: bool) -> FloatSamples:
    wave = audio.samples.astype(np.float32)
    return match_level(wave) if smart else wave


def _append(
    out: FloatSamples, wave: FloatSamples, gap: int, smart: bool, rate: int
) -> tuple[FloatSamples, SampleSpan]:
    overlap = min(int(CROSSFADE_LENGTH * rate), len(out), len(wave))
    if smart and gap < int(CROSSFADE_BELOW * rate) and overlap > 1:
        ramp = np.linspace(0, 1, overlap, dtype=np.float32)
        mixed = out[-overlap:] * (1 - ramp) + wave[:overlap] * ramp
        start = len(out) - overlap
        joined = np.concatenate([out[:-overlap], mixed, wave[overlap:]])
        return joined, (start, start + len(wave))
    start = len(out) + gap
    joined = np.concatenate([out, np.zeros(gap, dtype=np.float32), wave])
    return joined, (start, start + len(wave))
