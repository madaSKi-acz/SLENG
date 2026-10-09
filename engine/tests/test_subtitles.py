"""
Purpose:  Subtitle cues, SRT format and the ASS caption document.
Layer:    engine tests
Depends:  sleng.media
"""

from __future__ import annotations

import pytest

from sleng.media.ass import DEFAULT_LOOK, AssDocument, CaptionLayout
from sleng.media.subtitles import Cue, make_cues, split_cue_text, to_srt


def test_cue_text_breaks_at_sentences_then_spaces() -> None:
    assert split_cue_text("ក។ ខ គ ឃ", max_chars=3) == ["ក។", "ខ គ", "ឃ"]


def test_cues_share_chunk_time_by_length() -> None:
    cues = make_cues(["ab cd"], [(0.0, 2.0)], max_chars=2)
    assert [cue.text for cue in cues] == ["ab", "cd"]
    assert cues[0].end == pytest.approx(1.0)
    assert cues[1].end == pytest.approx(2.0)


def test_srt_format() -> None:
    srt = to_srt([Cue(0.0, 1.5, "សួស្តី"), Cue(61.0, 3725.25, "x")])
    assert srt.startswith("1\n00:00:00,000 --> 00:00:01,500\nសួស្តី\n")
    assert "2\n00:01:01,000 --> 01:02:05,250\nx\n" in srt


def test_ass_document_has_styles_title_card_and_karaoke() -> None:
    layout = CaptionLayout(1280, 720, "Kantumruy Pro", 54, (66, 133, 244))
    text = AssDocument(layout, DEFAULT_LOOK, karaoke=True).render(
        [Cue(3.0, 4.0, "ក ខ")], title="Hello", duration=4.0, intro=2.6
    )
    assert "PlayResX: 1280" in text
    assert "Style: Default,Kantumruy Pro,54," in text
    assert "Dialogue: 0,0:00:00.15,0:00:02.60,Card" in text
    assert "\\kf" in text
