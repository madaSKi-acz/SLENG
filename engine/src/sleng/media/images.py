"""
Purpose:  Small RGBA image generators for video layers (glow orb, gradient bar) and PNG saving.
Layer:    sleng.media
Exports:  RGBA, save_png, orb, gradient
Depends:  numpy, Pillow, sleng.media.palettes (RGB)
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np
import numpy.typing as npt
from PIL import Image

from sleng.media.palettes import RGB

RGBA = npt.NDArray[np.uint8]  # height x width x 4


def save_png(path: Path, rgba: RGBA) -> None:
    Image.fromarray(rgba, "RGBA").save(path)


def orb(size: int, rgb: RGB, strength: float) -> RGBA:
    """Soft round glow: one colour, alpha falling off like a gaussian."""
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    radius2 = ((x - size / 2) ** 2 + (y - size / 2) ** 2) / (size / 2) ** 2
    image = np.zeros((size, size, 4), dtype=np.uint8)
    image[..., :3] = rgb
    image[..., 3] = (np.exp(-radius2 * 3.2) * strength * 255).astype(np.uint8)
    return image


def gradient(width: int, height: int, palette: Sequence[RGB]) -> RGBA:
    """Opaque left-to-right gradient through the palette colours."""
    position = np.arange(width) / max(width - 1, 1)
    stops = np.linspace(0, 1, len(palette))
    channels = [np.interp(position, stops, [c[k] for c in palette]) for k in range(3)]
    image = np.zeros((height, width, 4), dtype=np.uint8)
    image[..., :3] = np.stack(channels, axis=1).astype(np.uint8)[None, :, :]
    image[..., 3] = 255
    return image
