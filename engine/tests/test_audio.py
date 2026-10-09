"""
Purpose:  Audio value object, pause rule, and timeline merging.
Layer:    engine tests
Depends:  numpy, sleng.audio, sleng.domain
"""

from __future__ import annotations

import numpy as np
import pytest

from sleng.audio.timeline import merge
from sleng.domain import Audio, InvalidInputError, PauseKind, PauseOptions

RATE = 1000


def tone(seconds: float) -> Audio:
    return Audio.from_float(np.full(int(seconds * RATE), 0.3), RATE)


def test_audio_is_read_only() -> None:
    audio = tone(0.1)
    with pytest.raises(ValueError):
        audio.samples[0] = 1


def test_gap_rule() -> None:
    pauses = PauseOptions(sentence=0.3, paragraph=0.8, smart=True)
    assert pauses.gap_after(PauseKind.SENTENCE) == 0.3
    assert pauses.gap_after(PauseKind.PARAGRAPH) == 0.8
    assert pauses.gap_after(PauseKind.PHRASE) == 0.1
    assert PauseOptions(sentence=0.3, smart=False).gap_after(PauseKind.PHRASE) == 0.3


def test_plain_merge_spans_include_gaps() -> None:
    timeline = merge([(tone(1.0), 0.5), (tone(2.0), 0.0)], smart=False)
    assert timeline.spans == ((0.0, 1.0), (1.5, 3.5))
    assert timeline.audio.duration == pytest.approx(3.5)


def test_smart_merge_crossfades_tiny_gaps() -> None:
    timeline = merge([(tone(1.0), 0.0), (tone(1.0), 0.0)], smart=True)
    assert timeline.audio.duration == pytest.approx(1.98)


def test_merge_without_parts_is_an_input_error() -> None:
    with pytest.raises(InvalidInputError):
        merge([])


def test_shifted_timeline_moves_every_span() -> None:
    timeline = merge([(tone(1.0), 0.2), (tone(1.0), 0.2)], smart=False).shifted(2.0)
    assert timeline.spans[0] == (2.0, 3.0)
    assert timeline.audio.duration == pytest.approx(4.2)
