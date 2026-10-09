"""
Purpose:  Pop scene background: mesh gradient, Y2K decorations (rings, squiggles, dots), grain.
Layer:    sleng.media.pop
Exports:  background
Depends:  Pillow, numpy, sleng.media.palettes
Invariants: the random draw order is fixed, so a seed always recreates the same design.
"""

from __future__ import annotations

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from sleng.media.palettes import RGB, PopColours, pop_colours

SUPERSAMPLE = 2
NIGHT = "night"
Point = tuple[float, float]


@dataclass(frozen=True)
class _Pen:
    """Drawing context for decorations on the supersampled canvas."""

    draw: ImageDraw.ImageDraw
    width: float
    height: float
    line: RGB

    @property
    def unit(self) -> float:
        return min(self.width, self.height)

    def rgba(self, alpha: int) -> tuple[int, int, int, int]:
        return (*self.line, alpha)


def background(width: int, height: int, palette: str, seed: int) -> Image.Image:
    """An RGB frame-sized image, new for every seed."""
    colours = pop_colours(palette)
    rng = random.Random(seed)
    image = _mesh(width, height, colours.mesh, rng).convert("RGBA")
    image.alpha_composite(_decorations(width, height, palette, colours, rng))
    return _grain(image, seed, dark=palette == NIGHT)


def _mesh(width: int, height: int, mesh: Sequence[RGB], rng: random.Random) -> Image.Image:
    """Base colour plus big blurred blobs."""
    blobs = Image.new("RGB", (width, height), mesh[0])
    draw = ImageDraw.Draw(blobs)
    for index in range(6):
        colour = mesh[(index + 1) % len(mesh)] if index < 4 else rng.choice(mesh)
        radius = max(width, height) * rng.uniform(0.25, 0.45)
        x, y = rng.uniform(-0.1, 1.1) * width, rng.uniform(-0.1, 1.1) * height
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=colour)
    return blobs.filter(ImageFilter.GaussianBlur(max(width, height) * 0.12))


def _decorations(
    width: int, height: int, palette: str, colours: PopColours, rng: random.Random
) -> Image.Image:
    canvas = Image.new("RGBA", (width * SUPERSAMPLE, height * SUPERSAMPLE))
    line = (200, 190, 255) if palette == NIGHT else (255, 255, 255)
    pen = _Pen(ImageDraw.Draw(canvas), width * SUPERSAMPLE, height * SUPERSAMPLE, line)
    _rings(pen, rng)
    _squiggles(pen, rng, colours.stickers)
    _dot_grids(pen, rng)
    _plus_signs(pen, rng)
    return canvas.resize((width, height), Image.Resampling.LANCZOS)


def _rings(pen: _Pen, rng: random.Random) -> None:
    for _ in range(rng.randint(2, 4)):
        radius = pen.unit * rng.uniform(0.08, 0.22)
        x, y = rng.uniform(0, pen.width), rng.uniform(0, pen.height)
        box = [x - radius, y - radius, x + radius, y + radius]
        pen.draw.ellipse(box, outline=pen.rgba(110), width=int(pen.unit * 0.006))


def _squiggles(pen: _Pen, rng: random.Random, palette: Sequence[RGB]) -> None:
    for _ in range(rng.randint(2, 3)):
        origin = (rng.uniform(0, pen.width), rng.uniform(0, pen.height))
        length = pen.unit * rng.uniform(0.2, 0.4)
        amplitude = pen.unit * rng.uniform(0.015, 0.03)
        phase, angle = rng.uniform(0, 6), rng.uniform(-0.6, 0.6)
        points = _wave(pen.unit, origin, (length, amplitude, phase), angle)
        colour = (*rng.choice(palette), 150)
        pen.draw.line(points, fill=colour, width=int(pen.unit * 0.008), joint="curve")


def _wave(
    unit: float, origin: Point, shape: tuple[float, float, float], angle: float
) -> list[Point]:
    (x0, y0), (length, amplitude, phase) = origin, shape
    cos, sin = math.cos(angle), math.sin(angle)
    points = []
    for index in range(60):
        u = index / 59 * length
        v = amplitude * math.sin(u / (unit * 0.03) + phase)
        points.append((x0 + u * cos - v * sin, y0 + u * sin + v * cos))
    return points


def _dot_grids(pen: _Pen, rng: random.Random) -> None:
    gap, radius = pen.unit * 0.025, pen.unit * 0.004
    for _ in range(rng.randint(1, 2)):
        x0, y0 = rng.uniform(0, pen.width * 0.8), rng.uniform(0, pen.height * 0.8)
        for column in range(6):
            for row in range(4):
                cx, cy = x0 + column * gap, y0 + row * gap
                box = [cx - radius, cy - radius, cx + radius, cy + radius]
                pen.draw.ellipse(box, fill=pen.rgba(140))


def _plus_signs(pen: _Pen, rng: random.Random) -> None:
    arm, stroke = pen.unit * 0.012, int(pen.unit * 0.004)
    for _ in range(rng.randint(4, 8)):
        cx, cy = rng.uniform(0, pen.width), rng.uniform(0, pen.height)
        pen.draw.line([(cx - arm, cy), (cx + arm, cy)], fill=pen.rgba(160), width=stroke)
        pen.draw.line([(cx, cy - arm), (cx, cy + arm)], fill=pen.rgba(160), width=stroke)


def _grain(image: Image.Image, seed: int, dark: bool) -> Image.Image:
    """Light film grain over the flattened RGB image."""
    noise_rng = np.random.default_rng(seed)
    noise = noise_rng.normal(0, 5 if dark else 6, (image.height, image.width, 1))
    pixels = np.asarray(image.convert("RGB"), np.float32) + noise.astype(np.float32)
    return Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8), "RGB")
