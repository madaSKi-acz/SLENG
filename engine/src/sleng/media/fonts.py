"""
Purpose:  Fonts for burned-in subtitles: the bundled Kantumruy Pro, or a custom TTF/OTF.
Layer:    sleng.media
Exports:  FontSet, FONT_DIR, DEFAULT_FAMILY, load_fonts, read_family
Depends:  standard library only (reads the font's 'name' table itself, no font library)
Notes:    Kantumruy Pro is SIL OFL 1.1 (assets/fonts/OFL.txt): free in videos, also commercial.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
DEFAULT_FAMILY = "Kantumruy Pro"
_FAMILY_IDS = (1, 16)  # name ids: font family, typographic family (preferred)
_PREFERRED_ID = 16


@dataclass(frozen=True)
class FontSet:
    """Font files to hand to libass and the family name the subtitles ask for."""

    files: tuple[Path, ...]
    family: str


def load_fonts(path: Path | None = None, family: str | None = None) -> FontSet:
    """A custom font replaces the bundled one; its family is read from the file if not given."""
    if path is None:
        return FontSet(tuple(sorted(FONT_DIR.glob("*.ttf"))), family or DEFAULT_FAMILY)
    return FontSet((path,), family or read_family(path) or path.stem)


def read_family(path: Path) -> str | None:
    """Family name from a TTF/OTF file, or None if it cannot be read."""
    try:
        return _family_from(path.read_bytes())
    except (OSError, struct.error, IndexError):
        return None


def _family_from(data: bytes) -> str | None:
    offset = _table_offset(data, b"name")
    if offset is None:
        return None
    count, strings = struct.unpack(">HH", data[offset + 2 : offset + 6])
    best: str | None = None
    for index in range(count):
        start = offset + 6 + 12 * index
        record = struct.unpack(">HHHHHH", data[start : start + 12])
        best = _better_name(data, offset + strings, record, best)
    return best


def _table_offset(data: bytes, tag: bytes) -> int | None:
    (count,) = struct.unpack(">H", data[4:6])
    for index in range(count):
        start = 12 + 16 * index
        name, _, offset, _ = struct.unpack(">4sIII", data[start : start + 16])
        if name == tag:
            return int(offset)
    return None


def _better_name(data: bytes, base: int, record: tuple[int, ...], best: str | None) -> str | None:
    platform, _, _, name_id, length, start = record
    if name_id not in _FAMILY_IDS:
        return best
    raw = data[base + start : base + start + length]
    text = raw.decode("utf-16-be" if platform in (0, 3) else "latin-1", "ignore")
    return text if text and (best is None or name_id == _PREFERRED_ID) else best
