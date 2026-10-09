"""
Purpose:  Builder for an ffmpeg -filter_complex graph: inputs, steps, and the current video label.
Layer:    sleng.media
Exports:  FilterGraph, FPS, even
Depends:  standard library only
"""

from __future__ import annotations

FPS = 25


def even(value: float) -> int:
    """Round down to an even integer (libx264 needs even sizes)."""
    return int(value) // 2 * 2


class FilterGraph:
    """Collects ffmpeg inputs and filter steps while tracking the latest video stream label."""

    def __init__(self) -> None:
        self.inputs: list[str] = []
        self.steps: list[str] = []
        self.current = ""
        self._input_count = 0
        self._label_count = 0

    def add_input(self, *args: str) -> str:
        """Append one input (its ffmpeg args); returns its video label, e.g. '[2:v]'."""
        self.inputs.extend(args)
        self._input_count += 1
        return f"[{self._input_count - 1}:v]"

    def add_image(self, filename: str) -> str:
        """A still image looped for the whole video."""
        return self.add_input("-loop", "1", "-framerate", str(FPS), "-i", filename)

    def start(self, label: str) -> None:
        self.current = label

    def chain(self, filters: str, *extra_inputs: str) -> None:
        """current (+ extra inputs) -> filters -> a new current label."""
        self._label_count += 1
        out = f"[v{self._label_count}]"
        self.steps.append(f"{self.current}{''.join(extra_inputs)}{filters}{out}")
        self.current = out

    def overlay(self, layer: str, x: str, y: str) -> None:
        """Put `layer` on top of the current stream at expressions x, y."""
        self.chain(f"overlay=x='{x}':y='{y}':format=auto", layer)

    def add_step(self, step: str) -> None:
        """A raw, self-labelled step that does not change the current stream."""
        self.steps.append(step)

    def script(self) -> str:
        return ";".join(self.steps)
