"""
Purpose:  Sticker silhouettes (heart, star, sparkle, circle, cloud, daisy, planet) as draw callables.
Layer:    sleng.media.pop
Exports:  Shape, Fill, heart, star, sparkle, circle, cloud, daisy, planet
Depends:  Pillow (ImageDraw), math
Notes:    Each factory takes the canvas size and returns draw(drawer, fill) for an s x s canvas.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from PIL import ImageDraw

Fill = int | tuple[int, ...]
Shape = Callable[[ImageDraw.ImageDraw, Fill], None]
Point = tuple[float, float]


def heart(size: float) -> Shape:
    points = [_heart_point(size, i / 80 * 2 * math.pi) for i in range(80)]
    return lambda draw, fill: draw.polygon(points, fill=fill)


def star(size: float, points: int = 5, inner: float = 0.45) -> Shape:
    centre, outer = size / 2, size * 0.46
    corners = []
    for i in range(points * 2):
        radius = outer if i % 2 == 0 else outer * inner
        angle = i * math.pi / points
        corners.append((centre + radius * math.sin(angle), centre - radius * math.cos(angle)))
    return lambda draw, fill: draw.polygon(corners, fill=fill)


def sparkle(size: float) -> Shape:
    """Concave four-point star."""
    centre, outer, waist = size / 2, size * 0.46, size * 0.1
    corners = []
    for i in range(4):
        tip, notch = i * math.pi / 2, i * math.pi / 2 + math.pi / 4
        corners.append((centre + outer * math.sin(tip), centre - outer * math.cos(tip)))
        corners.append((centre + waist * math.sin(notch), centre - waist * math.cos(notch)))
    return lambda draw, fill: draw.polygon(corners, fill=fill)


def circle(size: float, radius: float = 0.44) -> Shape:
    low, high = size * (0.5 - radius), size * (0.5 + radius)
    return lambda draw, fill: draw.ellipse([low, low, high, high], fill=fill)


def cloud(size: float) -> Shape:
    puffs = [(0.3, 0.58, 0.18), (0.5, 0.45, 0.24), (0.7, 0.56, 0.19), (0.5, 0.62, 0.18)]

    def draw_cloud(draw: ImageDraw.ImageDraw, fill: Fill) -> None:
        for cx, cy, r in puffs:
            box = [size * (cx - r), size * (cy - r), size * (cx + r), size * (cy + r)]
            draw.ellipse(box, fill=fill)
        base = [size * 0.14, size * 0.55, size * 0.86, size * 0.76]
        draw.rounded_rectangle(base, radius=size * 0.1, fill=fill)

    return draw_cloud


def daisy(size: float, petals: int = 8) -> Shape:
    centre, radius = size / 2, size * 0.17
    centres = [
        (centre + math.cos(a) * size * 0.26, centre + math.sin(a) * size * 0.26)
        for a in (i * 2 * math.pi / petals for i in range(petals))
    ]

    def draw_daisy(draw: ImageDraw.ImageDraw, fill: Fill) -> None:
        for px, py in centres:
            draw.ellipse([px - radius, py - radius, px + radius, py + radius], fill=fill)

    return draw_daisy


def planet(size: float) -> Shape:
    def draw_planet(draw: ImageDraw.ImageDraw, fill: Fill) -> None:
        draw.ellipse([size * 0.27, size * 0.27, size * 0.73, size * 0.73], fill=fill)
        ring = [size * 0.06, size * 0.42, size * 0.94, size * 0.62]
        draw.ellipse(ring, outline=fill, width=int(size * 0.06))

    return draw_planet


def _heart_point(size: float, t: float) -> Point:
    x = 16 * math.sin(t) ** 3
    y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
    return (size / 2 + x * size / 38, size * 0.47 + y * size / 38)
