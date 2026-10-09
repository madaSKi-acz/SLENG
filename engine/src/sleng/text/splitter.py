"""
Purpose:  Split text into Chunks (display + spoken text + the pause that follows each one).
Layer:    sleng.text (pure)
Exports:  split_text, chunks_from_lines
Depends:  sleng.domain.chunk, sleng.text.normalize, sleng.text.segment
Invariants: every returned chunk has non-empty spoken text; max_chars is measured on spoken text,
            where spelled-out numbers are longer than their digits.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from sleng.domain.chunk import Chunk, PauseKind, ScriptLine
from sleng.text.normalize import normalize
from sleng.text.segment import SENTENCE_ENDS, pack_words, split_sentences

_PARAGRAPHS = re.compile(r"\n\s*\n|\n")
_SPACES = re.compile(r"[ \t​]+")


def split_text(text: str, max_chars: int = 110) -> list[Chunk]:
    """Split at line breaks and sentence marks, then break long sentences at spaces."""
    paragraphs = _PARAGRAPHS.split(text)
    return [chunk for para in paragraphs for chunk in _split_paragraph(para, max_chars)]


def chunks_from_lines(lines: Iterable[ScriptLine]) -> list[Chunk]:
    """Already-split (maybe edited) lines -> chunks; lines with nothing to read are dropped."""
    chunks = []
    for line in lines:
        display = line.text.strip()
        spoken = normalize(display)
        if spoken:
            chunks.append(Chunk(display, spoken, line.pause))
    return chunks


def _split_paragraph(paragraph: str, max_chars: int) -> list[Chunk]:
    paragraph = _SPACES.sub(" ", paragraph).strip()
    sentences = split_sentences(paragraph)
    pieces = [piece for sentence in sentences for piece in _fit(sentence, max_chars)]
    readable = [(piece, normalize(piece)) for piece in pieces]
    readable = [(display, spoken) for display, spoken in readable if spoken]
    last = len(readable) - 1
    return [
        Chunk(display, spoken, _pause_after(display, index == last))
        for index, (display, spoken) in enumerate(readable)
    ]


def _fit(sentence: str, max_chars: int) -> list[str]:
    if len(normalize(sentence)) <= max_chars:
        return [sentence]
    return pack_words(sentence.split(" "), lambda line: len(normalize(line)) > max_chars)


def _pause_after(display: str, is_last: bool) -> PauseKind:
    if is_last:
        return PauseKind.PARAGRAPH
    return PauseKind.SENTENCE if display[-1] in SENTENCE_ENDS else PauseKind.PHRASE
