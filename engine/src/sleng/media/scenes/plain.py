"""
Purpose:  Plain black look: just the captions (no orbs, bars or progress bar).
Layer:    sleng.media.scenes
Exports:  PlainScene
Depends:  sleng.media.scenes.base
"""

from __future__ import annotations

from sleng.media.scenes.base import Scene, SceneContext, solid_background


class PlainScene(Scene):
    """Near-black background only."""

    progress = False

    def paint_background(self, ctx: SceneContext) -> None:
        ctx.graph.start(solid_background(ctx))
