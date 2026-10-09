"""
Purpose:  What gets read: a Script (raw text or edited lines) and the Chunks it is split into.
Layer:    sleng.domain (pure)
Exports:  PauseKind, Chunk, ScriptLine, Script
Depends:  standard library only
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PauseKind(str, Enum):
    """What follows a chunk: a mid-sentence cut, a sentence end, or a paragraph end."""

    PHRASE = "phrase"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"


@dataclass(frozen=True)
class Chunk:
    """One line to synthesize. `display` is shown in subtitles, `spoken` is what the voice reads."""

    display: str
    spoken: str
    pause: PauseKind


@dataclass(frozen=True)
class ScriptLine:
    """A line as the user sees (and maybe edited) it; `pause` comes from the earlier split."""

    text: str
    pause: PauseKind = PauseKind.SENTENCE


@dataclass(frozen=True)
class Script:
    """Raw text for the engine to split, or lines that were already split (they win if given)."""

    text: str = ""
    lines: tuple[ScriptLine, ...] = ()
    max_chars: int = 250
