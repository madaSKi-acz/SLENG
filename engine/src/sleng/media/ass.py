"""
Purpose:  ASS subtitle script for burned-in captions: optional karaoke, title or title card.
Layer:    sleng.media
Exports:  CaptionLook, CaptionLayout, AssDocument, DEFAULT_LOOK, POP_LOOK
Depends:  sleng.media.subtitles (Cue), sleng.media.palettes (RGB)
Notes:    With karaoke, words not yet spoken are dim and light up (\\kf) as they are spoken.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import NamedTuple

from sleng.media.palettes import RGB
from sleng.media.subtitles import Cue

_STYLE_FIELDS = (
    "Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
    "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, "
    "Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"
)
_EVENT_FIELDS = "Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
_TRANSPARENT = "&H00000000"
_SOFT_SHADOW = "&H70000000"
_PLUM_STROKE = "&H00301A22"
_CENTRE, _TOP_CENTRE = 5, 8


@dataclass(frozen=True)
class CaptionLook:
    """Caption colours: spoken words, not-yet-spoken words (karaoke), title card."""

    highlight: RGB = (255, 255, 255)
    dim: RGB = (128, 132, 138)
    card: RGB = (255, 255, 255)
    bold_outline: bool = False


DEFAULT_LOOK = CaptionLook()
POP_LOOK = CaptionLook(highlight=(255, 226, 60), dim=(255, 255, 255), bold_outline=True)


@dataclass(frozen=True)
class CaptionLayout:
    """Frame size, font and accent colour (used by the small title)."""

    width: int
    height: int
    font: str
    font_size: int
    accent: RGB


class _Style(NamedTuple):
    name: str
    size: int
    primary: str
    secondary: str
    outline_colour: str
    bold: int
    outline: int
    alignment: int
    margin_v: int

    def line(self, font: str, margin: int) -> str:
        values = (
            self.name, font, self.size, self.primary, self.secondary, self.outline_colour,
            _TRANSPARENT, self.bold, 0, 0, 0, 100, 100, 0, 0, 1, self.outline, 0,
            self.alignment, margin, margin, self.margin_v, 1,
        )  # fmt: skip
        return "Style: " + ",".join(str(value) for value in values)


class AssDocument:
    """Builds the .ass text libass burns into the video."""

    def __init__(self, layout: CaptionLayout, look: CaptionLook, karaoke: bool) -> None:
        self._layout = layout
        self._look = look
        self._karaoke = karaoke

    def render(self, cues: Sequence[Cue], title: str, duration: float, intro: float) -> str:
        """`intro` > 0 shows the title as a big card first; otherwise a small title stays on top."""
        events = self._title_events(title.strip(), duration, intro)
        events += [self._cue_event(cue) for cue in cues]
        return self._header() + "".join(events)

    def _header(self) -> str:
        layout = self._layout
        margin = int(layout.width * 0.08)
        styles = "\n".join(style.line(layout.font, margin) for style in self._styles())
        return (
            f"[Script Info]\nScriptType: v4.00+\nPlayResX: {layout.width}\n"
            f"PlayResY: {layout.height}\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
            f"[V4+ Styles]\nFormat: {_STYLE_FIELDS}\n{styles}\n\n"
            f"[Events]\nFormat: {_EVENT_FIELDS}\n"
        )

    def _styles(self) -> list[_Style]:
        layout, look = self._layout, self._look
        white, card, accent = _bgr(look.highlight), _bgr(look.card), _bgr(layout.accent)
        secondary = _bgr(look.dim) if self._karaoke else white
        outline = max(2, layout.font_size // (9 if look.bold_outline else 16))
        stroke = _PLUM_STROKE if look.bold_outline else _SOFT_SHADOW
        low, top = int(layout.height * 0.08), int(layout.height * 0.05)
        size = layout.font_size
        return [
            _Style("Default", size, white, secondary, stroke, 1, outline, _CENTRE, low),
            _Style("Card", int(size * 1.55), card, card, stroke, 1, outline, _CENTRE, low),
            _Style("Title", int(size * 0.6), accent, accent, _TRANSPARENT, 0, 0, _TOP_CENTRE, top),
        ]

    def _title_events(self, title: str, duration: float, intro: float) -> list[str]:
        if not title:
            return []
        text = _escape(title)
        if intro > 0:
            return [_event(0, (0.15, intro), "Card", f"{{\\fad(600,500)\\blur1}}{text}")]
        if duration > 0:
            return [_event(0, (0.0, duration), "Title", f"{{\\fad(600,600)}}{text}")]
        return []

    def _cue_event(self, cue: Cue) -> str:
        text = _escape(cue.text)
        body = _karaoke(text, cue.end - cue.start) if self._karaoke else text
        return _event(1, (cue.start, cue.end), "Default", f"{{\\fad(160,0)\\blur0.8}}{body}")


def _event(layer: int, span: tuple[float, float], style: str, text: str) -> str:
    start, end = _ass_time(span[0]), _ass_time(span[1])
    return f"Dialogue: {layer},{start},{end},{style},,0,0,0,,{text}\n"


def _karaoke(text: str, duration: float) -> str:
    """Spread the cue duration over its space-separated phrases (\\kf = smooth fill)."""
    words = text.split(" ")
    total = sum(len(word) for word in words) or 1
    centis = max(round(duration * 100), len(words))
    parts, used = [], 0
    for index, word in enumerate(words):
        last = index == len(words) - 1
        share = centis - used if last else max(1, round(centis * len(word) / total))
        used += share
        parts.append(f"{{\\kf{share}}}{word}" + ("" if last else " "))
    return "".join(parts)


def _escape(text: str) -> str:
    return text.replace("\\", "").replace("{", "(").replace("}", ")")


def _bgr(rgb: RGB) -> str:
    """(r, g, b) -> ASS colour &HAABBGGRR (AA=00 is opaque)."""
    red, green, blue = rgb
    return f"&H00{blue:02X}{green:02X}{red:02X}"


def _ass_time(seconds: float) -> str:
    cs = round(seconds * 100)
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"
