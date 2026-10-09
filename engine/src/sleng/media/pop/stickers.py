"""
Purpose:  Sticker sprites (white border, soft shadow, faces) and their floating placement.
Layer:    sleng.media.pop
Exports:  Sticker, stickers, make_sticker, KINDS
Depends:  Pillow, sleng.media.pop.shapes, sleng.media.palettes
Invariants: the random draw order is fixed, so a seed always recreates the same design.
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFilter

from sleng.media.palettes import RGB, pop_colours
from sleng.media.pop import shapes

SUPERSAMPLE = 2
INK = (34, 26, 48)  # dark outline / face colour
KINDS = ("heart", "star", "sparkle", "smiley", "daisy", "cloud", "planet")
Detail = Callable[[ImageDraw.ImageDraw, int], None]
LANCZOS = Image.Resampling.LANCZOS


@dataclass(frozen=True)
class Sticker:
    """A sprite plus its ffmpeg overlay position expressions (they bob and sway over time)."""

    image: Image.Image
    x: str
    y: str


def stickers(width: int, height: int, palette: str, seed: int, count: int = 10) -> list[Sticker]:
    """Stickers around the edges, clear of the captions (centre) and voice bars (bottom)."""
    colours = pop_colours(palette).stickers
    rng = random.Random(seed + 7)
    kinds = list(KINDS)
    rng.shuffle(kinds)
    placed: list[tuple[float, float]] = []
    out = []
    for index in range(count):
        kind = kinds[index % len(kinds)] if index < len(kinds) else rng.choice(kinds)
        scale = rng.uniform(0.04, 0.07) if kind == "sparkle" else rng.uniform(0.07, 0.12)
        image = make_sticker(kind, int(min(width, height) * scale), colours, rng)
        x, y = _place(rng, placed, width / height)
        placed.append((x, y))
        out.append(Sticker(image, *_motion(rng, x, y)))
    return out


def make_sticker(kind: str, size: int, colours: Sequence[RGB], rng: random.Random) -> Image.Image:
    colour = rng.choice(colours)  # drawn for every kind to keep the seed order stable
    canvas = size * SUPERSAMPLE
    makers: dict[str, Callable[[], Image.Image]] = {
        "heart": lambda: _render(size, shapes.heart(canvas), colour),
        "star": lambda: _render(size, shapes.star(canvas), colour),
        "sparkle": lambda: _render(size, shapes.sparkle(canvas), colour, border=False),
        "smiley": lambda: _render(size, shapes.circle(canvas), (255, 214, 40), _face),
        "daisy": lambda: _render(size, shapes.daisy(canvas), (255, 255, 255), _daisy_centre),
        "cloud": lambda: _render(size, shapes.cloud(canvas), (255, 255, 255)),
    }
    return makers.get(kind, lambda: _render(size, shapes.planet(canvas), colour))()


def _render(
    size: int, shape: shapes.Shape, colour: RGB, detail: Detail | None = None, border: bool = True
) -> Image.Image:
    canvas = size * SUPERSAMPLE
    pad = int(canvas * 0.12)
    mask = _mask(shape, canvas, pad)
    out = Image.new("RGBA", mask.size)
    if border:
        _add_border(out, mask, canvas)
    fill = Image.new("RGBA", mask.size, (*colour, 255))
    fill.putalpha(mask)
    out.alpha_composite(fill)
    if detail:
        _add_detail(out, detail, canvas, pad)
    final = size + int(size * 0.24)
    return out.resize((final, final), LANCZOS)


def _mask(shape: shapes.Shape, canvas: int, pad: int) -> Image.Image:
    silhouette = Image.new("L", (canvas, canvas))
    shape(ImageDraw.Draw(silhouette), 255)
    mask = Image.new("L", (canvas + pad * 2, canvas + pad * 2))
    mask.paste(silhouette, (pad, pad))
    return mask


def _add_border(out: Image.Image, mask: Image.Image, canvas: int) -> None:
    """White sticker edge with a soft drop shadow under it."""
    width = max(3, int(canvas * 0.045)) | 1
    outline = mask.filter(ImageFilter.MaxFilter(min(width * 2 + 1, 31)))
    blurred = outline.filter(ImageFilter.GaussianBlur(canvas * 0.03))
    shadow = Image.new("RGBA", out.size, (*INK, 0))
    shadow.putalpha(blurred.point(lambda value: int(value * 0.35)))
    out.alpha_composite(shadow, (int(canvas * 0.02), int(canvas * 0.035)))
    white = Image.new("RGBA", out.size, (255, 255, 255, 255))
    white.putalpha(outline)
    out.alpha_composite(white)


def _add_detail(out: Image.Image, detail: Detail, canvas: int, pad: int) -> None:
    layer = Image.new("RGBA", (canvas, canvas))
    detail(ImageDraw.Draw(layer), canvas)
    out.alpha_composite(layer, (pad, pad))


def _face(draw: ImageDraw.ImageDraw, s: int) -> None:
    """Smiley: two eyes, a smile and blush."""
    for eye in (0.38, 0.62):
        draw.ellipse([s * (eye - 0.04), s * 0.36, s * (eye + 0.04), s * 0.48], fill=(*INK, 255))
    smile = [s * 0.3, s * 0.38, s * 0.7, s * 0.7]
    draw.arc(smile, start=20, end=160, fill=(*INK, 255), width=int(s * 0.045))
    for cheek in (0.27, 0.73):
        blush = [s * (cheek - 0.06), s * 0.52, s * (cheek + 0.06), s * 0.58]
        draw.ellipse(blush, fill=(255, 120, 150, 140))


def _daisy_centre(draw: ImageDraw.ImageDraw, s: int) -> None:
    draw.ellipse([s * 0.36, s * 0.36, s * 0.64, s * 0.64], fill=(255, 196, 30, 255))


def _place(
    rng: random.Random, placed: list[tuple[float, float]], aspect: float
) -> tuple[float, float]:
    """Up to 200 random tries for a free spot; the last try is used if none is free."""
    x = y = 0.5
    for _ in range(200):
        x, y = rng.uniform(0.05, 0.95), rng.uniform(0.07, 0.9)
        if not _blocked(x, y, placed, aspect):
            break
    return x, y


def _blocked(x: float, y: float, placed: list[tuple[float, float]], aspect: float) -> bool:
    in_caption = abs(x - 0.5) < 0.32 and abs(y - 0.45) < 0.2
    in_bars = abs(x - 0.5) < 0.34 and y > 0.74
    crowded = any(math.hypot((x - px) * aspect, y - py) < 0.16 for px, py in placed)
    return in_caption or in_bars or crowded


def _motion(rng: random.Random, x: float, y: float) -> tuple[str, str]:
    bob, sway = rng.uniform(0.008, 0.02), rng.uniform(0.004, 0.012)
    f1, f2 = rng.uniform(0.5, 1.1), rng.uniform(0.3, 0.8)
    p1, p2 = rng.uniform(0, 6.3), rng.uniform(0, 6.3)
    x_expr = f"W*({x:.3f}+{sway:.3f}*sin(t*{f2:.2f}+{p2:.2f}))-w/2"
    y_expr = f"H*({y:.3f}+{bob:.3f}*sin(t*{f1:.2f}+{p1:.2f}))-h/2"
    return x_expr, y_expr
