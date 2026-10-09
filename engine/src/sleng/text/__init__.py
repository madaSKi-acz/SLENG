"""
Purpose:  Khmer text preparation: spell out numbers, normalise, split into speakable chunks.
Layer:    sleng.text (pure: no I/O, no state)
Exports:  normalize, spell_numbers, number_to_khmer, split_text, chunks_from_lines
Depends:  sleng.domain
"""

from sleng.text.normalize import normalize
from sleng.text.numbers import number_to_khmer, spell_numbers
from sleng.text.splitter import chunks_from_lines, split_text

__all__ = ["chunks_from_lines", "normalize", "number_to_khmer", "spell_numbers", "split_text"]
