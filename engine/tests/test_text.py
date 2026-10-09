"""
Purpose:  Khmer number spelling, normalisation and splitting.
Layer:    engine tests
Depends:  sleng.text, sleng.domain
"""

from __future__ import annotations

from sleng.domain import PauseKind, ScriptLine
from sleng.text import chunks_from_lines, normalize, number_to_khmer, spell_numbers, split_text
from sleng.text.numbers import KH_DIGITS


def test_number_to_khmer() -> None:
    assert number_to_khmer(65) == "ហុកសិបប្រាំ"
    assert number_to_khmer(385) == "បីរយ" + "ប៉ែតសិបប្រាំ"
    assert number_to_khmer(1600) == "មួយពាន់ប្រាំមួយរយ"
    assert number_to_khmer(101_000_000) == "មួយរយមួយលាន"
    assert number_to_khmer(10) == "ដប់"
    assert number_to_khmer(0) == "សូន្យ"


def test_spell_numbers_replaces_khmer_digits() -> None:
    spoken = spell_numbers("៦៥រូប")
    assert "៦៥" not in spoken
    assert "ហុកសិបប្រាំ" in spoken


def test_spell_numbers_decimal_and_padding() -> None:
    assert spell_numbers("3.5") == "បីក្បៀសប្រាំ"
    assert spell_numbers("a 12 b") == "a ដប់ពីរ b"
    assert spell_numbers("x12") == "x ដប់ពីរ"


def test_normalize_drops_brackets_and_soft_punctuation() -> None:
    assert normalize("(សួស្តី), «ពិភពលោក»") == "សួស្តី ពិភពលោក"
    assert normalize("  ()  ") == ""


def test_split_long_sample(sample_text: str) -> None:
    chunks = split_text(sample_text, 110)
    assert chunks
    assert all(len(chunk.spoken) <= 140 for chunk in chunks)
    digits = set("0123456789" + KH_DIGITS)
    assert not any(ch in digits for chunk in chunks for ch in chunk.spoken)
    assert chunks[-1].pause is PauseKind.PARAGRAPH


def test_split_marks_sentences_and_paragraphs() -> None:
    chunks = split_text("ក។ ខ។\nគ។", 110)
    assert [chunk.display for chunk in chunks] == ["ក។", "ខ។", "គ។"]
    assert [chunk.pause for chunk in chunks] == [
        PauseKind.SENTENCE,
        PauseKind.PARAGRAPH,
        PauseKind.PARAGRAPH,
    ]


def test_edited_lines_keep_their_pause_and_drop_empty_ones() -> None:
    lines = [ScriptLine("ក ១", PauseKind.PHRASE), ScriptLine("  "), ScriptLine("ខ")]
    chunks = chunks_from_lines(lines)
    assert [chunk.display for chunk in chunks] == ["ក ១", "ខ"]
    assert chunks[0].pause is PauseKind.PHRASE
    assert "មួយ" in chunks[0].spoken
