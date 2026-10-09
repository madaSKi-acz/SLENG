"""
Purpose:  Turn display text into what a voice should read: numbers spelled, noise characters gone.
Layer:    sleng.text (pure)
Exports:  normalize
Depends:  sleng.text.numbers
"""

from __future__ import annotations

import re

from sleng.text.numbers import spell_numbers

_ZERO_WIDTH_SPACE = "\u200b"
_BRACKETS_AND_QUOTES = re.compile(r"[()\[\]{}\"“”«»]")
_SOFT_PUNCTUATION = re.compile(r"[,;:]")
_SPACES = re.compile(r"[ \t]+")


def normalize(text: str) -> str:
    """Spoken form of `text`; an empty result means there is nothing to read."""
    text = spell_numbers(text).replace(_ZERO_WIDTH_SPACE, "")
    text = _BRACKETS_AND_QUOTES.sub(" ", text)
    text = _SOFT_PUNCTUATION.sub(" ", text)
    return _SPACES.sub(" ", text).strip()
