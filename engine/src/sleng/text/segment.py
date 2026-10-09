"""
Purpose:  Shared segmentation helpers: split at Khmer sentence marks, pack words into lines.
Layer:    sleng.text (pure)
Exports:  SENTENCE_ENDS, split_sentences, pack_words
Depends:  standard library only
Notes:    Khmer has no spaces inside phrases, so splitting at spaces never breaks letter shaping.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable

SENTENCE_ENDS = "។៕?!"
_AFTER_SENTENCE_END = re.compile(r"(?<=[។៕?!])")


def split_sentences(text: str) -> list[str]:
    """Pieces ending at ។ ៕ ? or ! (the mark stays with its sentence); blanks dropped."""
    return [part.strip() for part in _AFTER_SENTENCE_END.split(text) if part.strip()]


def pack_words(words: Iterable[str], too_long: Callable[[str], bool]) -> list[str]:
    """Greedy packing: keep adding words to a line until `too_long(line)` says stop."""
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}"
        if current and too_long(candidate):
            lines.append(current)
            current = word
        else:
            current = candidate.strip()
    if current:
        lines.append(current)
    return lines
