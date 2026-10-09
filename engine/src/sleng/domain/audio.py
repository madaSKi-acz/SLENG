"""
Purpose:  Audio value object (mono int16 samples + sample rate) and a merged narration Timeline.
Layer:    sleng.domain (pure)
Exports:  Audio, Timeline, Span, Samples, FloatSamples
Depends:  numpy
Invariants: samples are mono int16 and read-only; the rate always travels with its samples.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

Samples = npt.NDArray[np.int16]
FloatSamples = npt.NDArray[np.float32]
Span = tuple[float, float]


@dataclass(frozen=True, eq=False)
class Audio:
    """Mono int16 speech. Immutable: the sample buffer is made read-only on creation."""

    samples: Samples
    rate: int

    def __post_init__(self) -> None:
        self.samples.setflags(write=False)

    @classmethod
    def from_float(cls, wave: npt.ArrayLike, rate: int) -> Audio:
        """Float samples in [-1, 1] -> int16 audio; anything outside the range is clipped."""
        return cls((np.clip(wave, -1, 1) * 32767).astype(np.int16), rate)

    @classmethod
    def silence(cls, seconds: float, rate: int) -> Audio:
        return cls(np.zeros(int(seconds * rate), dtype=np.int16), rate)

    @classmethod
    def join(cls, parts: list[Audio]) -> Audio:
        """Plain concatenation; every part must share the first part's rate."""
        return cls(np.concatenate([part.samples for part in parts]), parts[0].rate)

    @property
    def duration(self) -> float:
        return len(self.samples) / self.rate

    def to_float(self) -> FloatSamples:
        """int16 -> float32 in [-1, 1)."""
        return (self.samples / 32768).astype(np.float32)

    def prepend_silence(self, seconds: float) -> Audio:
        pad = np.zeros(int(seconds * self.rate), dtype=np.int16)
        return Audio(np.concatenate([pad, self.samples]), self.rate)


@dataclass(frozen=True, eq=False)
class Timeline:
    """Merged narration plus the (start, end) seconds of every chunk inside it."""

    audio: Audio
    spans: tuple[Span, ...]

    def shifted(self, seconds: float) -> Timeline:
        """Silence first (e.g. under a title card); every span moves later by the same amount."""
        spans = tuple((start + seconds, end + seconds) for start, end in self.spans)
        return Timeline(self.audio.prepend_silence(seconds), spans)
