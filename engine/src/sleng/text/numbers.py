"""
Purpose:  Spell Khmer and ASCII digit runs (with , and . separators) as Khmer words.
Layer:    sleng.text (pure)
Exports:  KH_DIGITS, number_to_khmer, spell_numbers
Depends:  standard library only
Notes:    "1,234.5" (thousands + decimal) loses its dot and reads as 12345, as before the refactor.
"""

from __future__ import annotations

import re

KH_DIGITS = "០១២៣៤៥៦៧៨៩"
_DIGIT_WORDS = ["សូន្យ", "មួយ", "ពីរ", "បី", "បួន", "ប្រាំ", "ប្រាំមួយ", "ប្រាំពីរ", "ប្រាំបី", "ប្រាំបួន"]
_TENS = {
    2: "ម្ភៃ", 3: "សាមសិប", 4: "សែសិប", 5: "ហាសិប",
    6: "ហុកសិប", 7: "ចិតសិប", 8: "ប៉ែតសិប", 9: "កៅសិប",
}  # fmt: skip
_UNITS = [(10**6, "លាន"), (10**5, "សែន"), (10**4, "ម៉ឺន"), (10**3, "ពាន់"), (100, "រយ")]
_DECIMAL_MARK = "ក្បៀស"
_KH_TO_ASCII = {ord(digit): str(value) for value, digit in enumerate(KH_DIGITS)}
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
_DECIMAL = re.compile(r"\d+\.\d+")


def number_to_khmer(number: int) -> str:
    """Non-negative integer -> Khmer words (e.g. 65 -> ហុកសិបប្រាំ)."""
    if number < 10:
        return _DIGIT_WORDS[number]
    if number < 100:
        tens, ones = divmod(number, 10)
        head = "ដប់" if tens == 1 else _TENS[tens]
        return head + (_DIGIT_WORDS[ones] if ones else "")
    for value, word in _UNITS:
        if number >= value:
            quotient, rest = divmod(number, value)
            return number_to_khmer(quotient) + word + (number_to_khmer(rest) if rest else "")
    raise ValueError(number)


def spell_numbers(text: str) -> str:
    """Every digit run in `text` replaced by Khmer words."""
    return _NUMBER.sub(_replace, text.translate(_KH_TO_ASCII))


def _replace(match: re.Match[str]) -> str:
    words = _number_words(match.group(0))
    return _pad(words, match.string, match.start(), match.end())


def _number_words(raw: str) -> str:
    if "." in raw and not _DECIMAL.fullmatch(raw):
        raw = raw.replace(".", "")
    if _DECIMAL.fullmatch(raw):
        whole, fraction = raw.split(".")
        digits = "".join(_DIGIT_WORDS[int(digit)] for digit in fraction)
        return f"{number_to_khmer(int(whole))}{_DECIMAL_MARK}{digits}"
    return number_to_khmer(int(raw.replace(",", "")))


def _pad(words: str, text: str, start: int, end: int) -> str:
    """Add a space only next to non-Khmer text (Khmer words are written without spaces)."""
    left = " " if start > 0 and _needs_space(text[start - 1]) else ""
    right = " " if end < len(text) and _needs_space(text[end]) else ""
    return left + words + right


def _needs_space(neighbour: str) -> bool:
    is_khmer = "ក" <= neighbour <= "៿"
    return not is_khmer and not neighbour.isspace()
