"""
Purpose:  The Scene strategy interface and the context a scene paints into.
Layer:    sleng.media.scenes
Exports:  Scene, SceneContext, solid_background, BASE_BACKGROUND
Depends:  sleng.media.graph
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from sleng.media.graph import FPS, FilterGraph

BASE_BACKGROUND = (19, 19, 20)  # near-black


@dataclass(frozen=True)
class SceneContext:
    """Where and what a scene paints: the graph, a temp folder for images, frame and palette."""

    graph: FilterGraph
    workdir: Path
    width: int
    height: int
    palette: str
    seed: int
    duration: float


class Scene(ABC):
    """One video look. The renderer adds voice bars, progress bar and captions around it."""

    bars = False  # draw the voice bars
    progress = True  # allow the progress bar

    @abstractmethod
    def paint_background(self, ctx: SceneContext) -> None:
        """Add the background inputs and leave ctx.graph.current on the painted frame."""

    def paint_behind_bars(self, ctx: SceneContext, bars_size: tuple[int, int]) -> None:
        """Optional layer under the voice bars (pop scenes draw a glass pill)."""
        return None


def solid_background(ctx: SceneContext) -> str:
    """A near-black colour source for the whole duration; returns its label."""
    red, green, blue = BASE_BACKGROUND
    colour = f"0x{red:02X}{green:02X}{blue:02X}"
    source = f"color=c={colour}:s={ctx.width}x{ctx.height}:r={FPS}:d={ctx.duration:.2f}"
    return ctx.graph.add_input("-f", "lavfi", "-i", source)
