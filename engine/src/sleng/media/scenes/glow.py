"""
Purpose:  Glow look (three slowly drifting colour orbs) and Studio look (glow + voice bars).
Layer:    sleng.media.scenes
Exports:  GlowScene, StudioScene
Depends:  sleng.media.scenes.base, sleng.media.images, sleng.media.palettes, sleng.media.graph
"""

from __future__ import annotations

from sleng.media.graph import even
from sleng.media.images import orb, save_png
from sleng.media.palettes import colours
from sleng.media.scenes.base import Scene, SceneContext, solid_background

# Orb centre x, y as fractions of the frame, drifting with time t (ffmpeg expressions).
ORB_MOTION = (
    ("0.14+0.10*sin(t*0.35)", "0.18+0.08*cos(t*0.28)"),
    ("0.86+0.08*sin(t*0.30+2)", "0.28+0.10*sin(t*0.22+1)"),
    ("0.52+0.12*sin(t*0.25+4)", "1.02+0.06*cos(t*0.33)"),
)
ORB_STRENGTH = (0.60, 0.60, 0.50)


class GlowScene(Scene):
    """Dark base with three soft glows in the palette colours."""

    def paint_background(self, ctx: SceneContext) -> None:
        ctx.graph.start(solid_background(ctx))
        ctx.graph.chain("format=rgba")
        size = even(max(ctx.width, ctx.height) * 0.95)
        orbs = zip(colours(ctx.palette), ORB_MOTION, ORB_STRENGTH, strict=True)
        for index, (rgb, (x, y), strength) in enumerate(orbs, 1):
            name = f"orb{index}.png"
            save_png(ctx.workdir / name, orb(size, rgb, strength))
            ctx.graph.overlay(ctx.graph.add_image(name), f"W*({x})-w/2", f"H*({y})-h/2")


class StudioScene(GlowScene):
    """Glow plus rounded voice bars that follow the narration."""

    bars = True
