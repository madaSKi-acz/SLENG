"""
Purpose:  Frosted rounded "glass" pill that sits behind the voice bars in pop scenes.
Layer:    sleng.media.pop
Exports:  glass_pill
Depends:  Pillow
"""

from __future__ import annotations

from PIL import Image, ImageDraw

SUPERSAMPLE = 2


def glass_pill(width: int, height: int, dark: bool = False) -> Image.Image:
    """Translucent white pill; fainter on dark palettes."""
    canvas = Image.new("RGBA", (width * SUPERSAMPLE, height * SUPERSAMPLE))
    fill = (255, 255, 255, 34 if dark else 70)
    outline = (255, 255, 255, 80 if dark else 150)
    box = [0, 0, width * SUPERSAMPLE - 1, height * SUPERSAMPLE - 1]
    radius = height * SUPERSAMPLE / 2
    ImageDraw.Draw(canvas).rounded_rectangle(
        box, radius=radius, fill=fill, outline=outline, width=2 * SUPERSAMPLE
    )
    return canvas.resize((width, height), Image.Resampling.LANCZOS)
