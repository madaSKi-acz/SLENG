"""
Purpose:  Subtitle cues from chunk texts and their timings, and the SRT file format.
Layer:    sleng.media
Exports:  Cue, split_cue_text, make_cues, to_srt
Depends:  sleng.text.segment, sleng.domain.audio (Span)
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import NamedTuple

from sleng.domain.audio import Span
from sleng.text.segment import pack_words, split_sentences

DEFAULT_CUE_CHARS = 60


class Cue(NamedTuple):
    """One subtitle line on screen from `start` to `end` seconds."""

    start: float
    end: float
    text: str


def split_cue_text(text: str, max_chars: int = DEFAULT_CUE_CHARS) -> list[str]:
    """Short subtitle lines: break at sentence ends, then at spaces."""
    lines: list[str] = []
    for sentence in split_sentences(text):
        lines += pack_words(sentence.split(" "), lambda line: len(line) > max_chars)
    return lines


def make_cues(
    displays: Sequence[str], spans: Sequence[Span], max_chars: int = DEFAULT_CUE_CHARS
) -> list[Cue]:
    """One or more cues per chunk; a chunk's time is shared by its lines by their length."""
    cues: list[Cue] = []
    for text, (start, end) in zip(displays, spans, strict=True):
        cues += _spread(split_cue_text(text, max_chars), start, end)
    return cues


def to_srt(cues: Sequence[Cue]) -> str:
    """SubRip text (for CapCut, Premiere, DaVinci...)."""
    blocks = (
        f"{index}\n{_srt_time(cue.start)} --> {_srt_time(cue.end)}\n{cue.text}\n"
        for index, cue in enumerate(cues, 1)
    )
    return "\n".join(blocks)


def _spread(lines: list[str], start: float, end: float) -> list[Cue]:
    total = sum(len(line) for line in lines) or 1
    cues, cursor = [], start
    for line in lines:
        length = (end - start) * len(line) / total
        cues.append(Cue(cursor, cursor + length, line))
        cursor += length
    return cues


def _srt_time(seconds: float) -> str:
    ms = round(seconds * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
