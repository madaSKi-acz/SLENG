"""
Purpose:  Video looks as interchangeable strategies; pick one with scene_for(theme).
Layer:    sleng.media.scenes
Exports:  Scene, SceneContext, scene_for
Depends:  sleng.media.scenes.{base, plain, glow, pop}, sleng.domain.options
Notes:    Adding a look = one new Scene subclass + one entry in SCENES. Nothing else changes.
"""

from sleng.domain.options import VideoTheme
from sleng.media.scenes.base import Scene, SceneContext
from sleng.media.scenes.glow import GlowScene, StudioScene
from sleng.media.scenes.plain import PlainScene
from sleng.media.scenes.pop import PopScene

SCENES: dict[VideoTheme, Scene] = {
    VideoTheme.PLAIN: PlainScene(),
    VideoTheme.GLOW: GlowScene(),
    VideoTheme.STUDIO: StudioScene(),
    VideoTheme.POP: PopScene(),
}


def scene_for(theme: VideoTheme) -> Scene:
    return SCENES[theme]


__all__ = ["SCENES", "Scene", "SceneContext", "scene_for"]
