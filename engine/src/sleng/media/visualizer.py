"""
Purpose:  Voice-bar frames: rounded bars whose loudness ripples out from the centre.
Layer:    sleng.media
Exports:  BarVisualizer
Depends:  numpy, sleng.media.images (gradient), sleng.media.envelope
Notes:    Frames are raw RGBA bytes streamed to ffmpeg's stdin; bars shrink to dots in silence.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence

import numpy as np

from sleng.domain.audio import FloatSamples
from sleng.media.envelope import ENVELOPE_STEP
from sleng.media.images import gradient
from sleng.media.palettes import RGB

BAR_COUNT = 31
RIPPLE_DELAY = 0.045  # seconds of extra lag per bar away from the centre
OPACITY = 235


class BarVisualizer:
    """Precomputes the bar geometry once; `frames()` then yields one frame per video frame."""

    def __init__(
        self, envelope: FloatSamples, size: tuple[int, int], palette: Sequence[RGB]
    ) -> None:
        width, height = size
        slot = width / BAR_COUNT
        self._envelope = envelope
        self._height = height
        self._bar_width = max(4, int(slot * 0.55))
        bar_of_column = (np.arange(width) / slot).astype(int).clip(0, BAR_COUNT - 1)
        self._inside = np.arange(width) - bar_of_column * slot - (slot - self._bar_width) / 2
        self._valid = (self._inside >= 0) & (self._inside < self._bar_width)
        self._distance = np.abs(bar_of_column - BAR_COUNT // 2)
        self._taper = 1 - (self._distance / (BAR_COUNT // 2 + 1)) ** 2 * 0.55
        self._rows = np.abs(np.arange(height)[:, None] - (height - 1) / 2)
        self._frame = gradient(width, height, palette)

    @staticmethod
    def frame_count(seconds: float, fps: int) -> int:
        return int(seconds * fps) + 1

    def frames(self, seconds: float, fps: int) -> Iterator[bytes]:
        for index in range(self.frame_count(seconds, fps)):
            yield self._render(index / fps)

    def _render(self, now: float) -> bytes:
        half = self._heights(now) / 2
        alpha = self._alpha(half) * self._valid[None, :] * OPACITY
        self._frame[..., 3] = alpha.astype(np.uint8)
        return self._frame.tobytes()

    def _heights(self, now: float) -> FloatSamples:
        """Outer bars show slightly older loudness; never smaller than a dot."""
        lag = (now - self._distance * RIPPLE_DELAY) / ENVELOPE_STEP
        index = np.clip(lag.astype(int), 0, len(self._envelope) - 1)
        level = self._envelope[index] * (lag >= 0)
        return np.maximum(self._bar_width, level * self._taper * self._height)

    def _alpha(self, half: FloatSamples) -> FloatSamples:
        """Bar body with a 1 px soft edge and rounded caps (circle of radius bar_width / 2)."""
        rows, radius = self._rows, self._bar_width / 2
        body = np.clip(half[None, :] - rows + 1, 0, 1)
        centre_offset = self._inside - self._bar_width / 2 + 0.5
        cap_half = np.sqrt(np.maximum(radius * radius - centre_offset * centre_offset, 0))
        into_cap = np.clip(rows - (half[None, :] - radius), 0, None)
        inside_bar = half[None, :] - rows + 1 > 0
        rounded = np.clip(cap_half[None, :] - into_cap + 1, 0, 1) * inside_bar
        return np.where(into_cap > 0, rounded, body)
