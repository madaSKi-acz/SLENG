"""
Purpose:  Cute, modern video art drawn from code (no stock assets, no national symbols).
Layer:    sleng.media.pop
Exports:  background, stickers, Sticker, glass_pill
Depends:  Pillow, numpy, sleng.media.palettes
Notes:    Every video gets a new layout from a seed: a mesh gradient with grain, Y2K decorations,
          floating stickers around the edges (centre kept clear for captions), a glass pill.
"""

from sleng.media.pop.background import background
from sleng.media.pop.glass import glass_pill
from sleng.media.pop.stickers import Sticker, stickers

__all__ = ["Sticker", "background", "glass_pill", "stickers"]
