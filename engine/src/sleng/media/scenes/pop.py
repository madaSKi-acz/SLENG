"""
Purpose:  Pop look: pastel mesh background, floating stickers, voice bars on a glass pill.
Layer:    sleng.media.scenes
Exports:  PopScene
Depends:  sleng.media.pop, sleng.media.scenes.base, sleng.media.graph
"""

from __future__ import annotations

from sleng.media.graph import even
from sleng.media.pop import background, glass_pill, stickers
from sleng.media.scenes.base import Scene, SceneContext

BARS_LIFT = 0.07  # voice bars sit this fraction of the height above the bottom edge


class PopScene(Scene):
    """A new cute design for every seed."""

    bars = True

    def paint_background(self, ctx: SceneContext) -> None:
        image = background(ctx.width, ctx.height, ctx.palette, ctx.seed)
        image.save(ctx.workdir / "bg.png")
        ctx.graph.start(ctx.graph.add_image("bg.png"))
        ctx.graph.chain("format=rgba")
        sprites = stickers(ctx.width, ctx.height, ctx.palette, ctx.seed)
        for index, sticker in enumerate(sprites, 1):
            name = f"sticker{index}.png"
            sticker.image.save(ctx.workdir / name)
            ctx.graph.overlay(ctx.graph.add_image(name), sticker.x, sticker.y)

    def paint_behind_bars(self, ctx: SceneContext, bars_size: tuple[int, int]) -> None:
        bars_width, bars_height = bars_size
        width, height = even(bars_width * 1.12), even(bars_height * 1.5)
        glass_pill(width, height, dark=ctx.palette == "night").save(ctx.workdir / "pill.png")
        lift = int(ctx.height * BARS_LIFT - (height - bars_height) / 2)
        ctx.graph.overlay(ctx.graph.add_image("pill.png"), "(W-w)/2", f"H-h-{lift}")
