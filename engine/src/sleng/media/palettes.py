"""
Purpose:  Every colour palette used by videos: accent triples and the pop-art scene colours.
Layer:    sleng.media
Exports:  RGB, ACCENT_PALETTES, POP_COLOURS, PopColours, DEFAULT_PALETTE, DEFAULT_POP_PALETTE,
          resolve_palette, colours, accent, pop_colours, palette_groups
Depends:  sleng.domain.options
Invariants: this is the only palette list; the UI reads it through GET /api/v1/options.
"""

from __future__ import annotations

from dataclasses import dataclass

from sleng.domain.options import VideoTheme

RGB = tuple[int, int, int]
Triple = tuple[RGB, RGB, RGB]

# name -> three colours for glow orbs, voice bars and the progress bar (first = accent)
ACCENT_PALETTES: dict[str, Triple] = {
    "gemini": ((66, 133, 244), (155, 114, 203), (217, 101, 112)),
    "blue": ((91, 140, 255), (130, 100, 255), (60, 200, 255)),
    "gold": ((245, 185, 66), (255, 130, 60), (255, 220, 120)),
    "green": ((52, 211, 153), (60, 170, 255), (150, 230, 120)),
    "pink": ((244, 114, 182), (180, 100, 255), (255, 150, 120)),
    "white": ((235, 238, 245), (180, 190, 210), (140, 150, 170)),
    "candy": ((255, 92, 170), (160, 110, 255), (90, 180, 255)),
    "mint": ((20, 190, 140), (80, 140, 255), (255, 95, 135)),
    "sunset": ((255, 70, 115), (110, 80, 255), (255, 160, 60)),
    "night": ((255, 80, 200), (70, 235, 255), (185, 255, 70)),
}
DEFAULT_PALETTE = "gemini"
DEFAULT_POP_PALETTE = "candy"


@dataclass(frozen=True)
class PopColours:
    """Pop scene colours: soft mesh-gradient blobs and bright sticker fills."""

    mesh: tuple[RGB, ...]
    stickers: tuple[RGB, ...]


POP_COLOURS: dict[str, PopColours] = {
    "candy": PopColours(
        ((255, 182, 213), (203, 170, 255), (160, 210, 255), (255, 214, 236)),
        ((255, 92, 170), (255, 205, 0), (90, 180, 255), (160, 110, 255), (255, 130, 90)),
    ),
    "mint": PopColours(
        ((178, 245, 220), (255, 245, 170), (255, 205, 178), (190, 230, 255)),
        ((20, 190, 140), (255, 160, 40), (255, 95, 135), (80, 140, 255), (255, 210, 0)),
    ),
    "sunset": PopColours(
        ((255, 170, 110), (255, 120, 160), (160, 110, 255), (255, 210, 140)),
        ((255, 225, 70), (255, 70, 115), (110, 80, 255), (50, 210, 190), (255, 255, 255)),
    ),
    "night": PopColours(
        ((26, 20, 64), (128, 44, 178), (32, 96, 182), (76, 32, 140)),
        ((255, 80, 200), (70, 235, 255), (185, 255, 70), (255, 215, 50), (175, 125, 255)),
    ),
}


def resolve_palette(theme: VideoTheme, name: str) -> str:
    """The palette actually used: pop scenes need a pop palette, unknown names fall back."""
    if theme is VideoTheme.POP:
        return name if name in POP_COLOURS else DEFAULT_POP_PALETTE
    return name if name in ACCENT_PALETTES else DEFAULT_PALETTE


def colours(name: str) -> Triple:
    return ACCENT_PALETTES.get(name, ACCENT_PALETTES[DEFAULT_PALETTE])


def accent(name: str) -> RGB:
    return colours(name)[0]


def pop_colours(name: str) -> PopColours:
    return POP_COLOURS.get(name, POP_COLOURS[DEFAULT_POP_PALETTE])


def palette_groups() -> list[tuple[str, str]]:
    """(palette name, "pop" | "other") for every palette, pop palettes first."""
    pop = [(name, "pop") for name in POP_COLOURS]
    other = [(name, "other") for name in ACCENT_PALETTES if name not in POP_COLOURS]
    return pop + other
