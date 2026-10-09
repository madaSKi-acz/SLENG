"""
Purpose:  Encode narration + scene + voice bars + progress bar + burned-in captions into an MP4.
Layer:    sleng.media
Exports:  VideoRenderer, RenderJob, Progress
Depends:  sleng.infra.ffmpeg, sleng.media.{graph, scenes, visualizer, envelope, images, fonts}
Notes:    Input 0 is always the narration WAV. Voice-bar frames are streamed to ffmpeg's stdin.
"""

from __future__ import annotations

import contextlib
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from sleng.audio.wav import encode_wav
from sleng.domain.audio import Audio
from sleng.domain.options import VideoOptions
from sleng.infra.ffmpeg import Ffmpeg, FfmpegError
from sleng.media.envelope import loudness_envelope
from sleng.media.fonts import FontSet
from sleng.media.graph import FPS, FilterGraph, even
from sleng.media.images import gradient, save_png
from sleng.media.palettes import colours
from sleng.media.scenes import Scene, SceneContext, scene_for
from sleng.media.visualizer import BarVisualizer

Progress = Callable[[float], None]
TAIL_SECONDS = 0.3
BARS_LIFT = 0.07
OUTPUT = "out.mp4"
ENCODE_ARGS = (
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
)  # fmt: skip


def _ignore(_: float) -> None:
    return None


@dataclass(frozen=True, eq=False)
class RenderJob:
    """Everything one render needs. `palette` is already resolved for the theme."""

    audio: Audio
    captions: str | None
    options: VideoOptions
    palette: str
    seed: int


class VideoRenderer:
    """Builds the ffmpeg filter graph for a scene and runs the encode."""

    def __init__(self, ffmpeg: Ffmpeg, fonts: FontSet) -> None:
        self._ffmpeg = ffmpeg
        self._fonts = fonts

    def render(self, job: RenderJob, out_path: Path, on_progress: Progress = _ignore) -> None:
        """Write the MP4 to `out_path`; `on_progress` receives 0..1 while frames are encoded."""
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _context(job, Path(tmp))
            bars = self._compose(ctx, job)
            self._encode(ctx, bars, on_progress)
            shutil.move(str(ctx.workdir / OUTPUT), out_path)
        on_progress(1.0)

    def _compose(self, ctx: SceneContext, job: RenderJob) -> BarVisualizer | None:
        scene = scene_for(job.options.theme)
        scene.paint_background(ctx)
        bars = _add_bars(ctx, scene, job.audio) if scene.bars else None
        if job.options.progress_bar and scene.progress:
            _add_progress_bar(ctx)
        self._add_captions(ctx, job.captions)
        return bars

    def _add_captions(self, ctx: SceneContext, captions: str | None) -> None:
        if not captions:
            ctx.graph.chain("null")
            return
        (ctx.workdir / "subs.ass").write_text(captions, encoding="utf-8")
        fonts_dir = ctx.workdir / "fonts"
        fonts_dir.mkdir()
        for font in self._fonts.files:
            shutil.copy(font, fonts_dir / font.name)
        ctx.graph.chain("ass=subs.ass:fontsdir=fonts")  # relative paths: no Windows drive colons

    def _encode(
        self, ctx: SceneContext, bars: BarVisualizer | None, on_progress: Progress
    ) -> None:
        stdin = subprocess.PIPE if bars else subprocess.DEVNULL
        log_path = ctx.workdir / "ffmpeg.log"
        with log_path.open("w+", encoding="utf-8", errors="replace") as log:
            process = self._ffmpeg.spawn(_output_args(ctx), ctx.workdir, stdin, log)
            if bars:
                _feed(process, bars, ctx.duration, on_progress)
            code = process.wait()
            log.seek(0)
            errors = log.read()
        if code != 0 or not (ctx.workdir / OUTPUT).exists():
            raise FfmpegError("ffmpeg failed: " + errors[-700:])


def _context(job: RenderJob, workdir: Path) -> SceneContext:
    (workdir / "audio.wav").write_bytes(encode_wav(job.audio))
    graph = FilterGraph()
    graph.add_input("-i", "audio.wav")
    options = job.options
    duration = job.audio.duration + TAIL_SECONDS
    return SceneContext(
        graph, workdir, options.width, options.height, job.palette, job.seed, duration
    )


def _add_bars(ctx: SceneContext, scene: Scene, audio: Audio) -> BarVisualizer:
    """Rounded voice bars with a soft glow, bottom centre; returns the frame source."""
    side = min(ctx.width, ctx.height)
    width, height = even(side * 0.62), even(side * 0.13)
    raw = ("-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{width}x{height}")
    pipe = ctx.graph.add_input(*raw, "-framerate", str(FPS), "-i", "pipe:0")
    blur = max(4, height // 10)
    glow = f"[vzg]gblur=sigma={blur}[glow]"
    ctx.graph.add_step(f"{pipe}split[vz][vzg];{glow};[glow][vz]overlay=format=auto[bars]")
    scene.paint_behind_bars(ctx, (width, height))
    ctx.graph.overlay("[bars]", "(W-w)/2", f"H-h-{int(ctx.height * BARS_LIFT)}")
    return BarVisualizer(loudness_envelope(audio), (width, height), colours(ctx.palette))


def _add_progress_bar(ctx: SceneContext) -> None:
    """Thin gradient bar along the bottom that grows with the audio, over a faint track."""
    height = max(4, ctx.height // 140)
    save_png(ctx.workdir / "bar.png", gradient(ctx.width, height, colours(ctx.palette)))
    bar = ctx.graph.add_image("bar.png")
    top = str(ctx.height - height)
    ctx.graph.add_step(f"color=c=white@0.10:s={ctx.width}x{height}:r={FPS},format=rgba[track]")
    ctx.graph.overlay("[track]", "0", top)
    ctx.graph.overlay(bar, f"-w+w*t/{ctx.duration:.2f}", top)


def _output_args(ctx: SceneContext) -> list[str]:
    graph = ctx.graph
    filters = ["-filter_complex", graph.script()]
    mapping = ["-map", graph.current, "-map", "0:a", "-t", f"{ctx.duration:.2f}"]
    return ["-y", *graph.inputs, *filters, *mapping, *ENCODE_ARGS, OUTPUT]


def _feed(
    process: subprocess.Popen[bytes], bars: BarVisualizer, seconds: float, on_progress: Progress
) -> None:
    stdin = process.stdin
    if stdin is None:
        return
    total = bars.frame_count(seconds, FPS)
    with contextlib.suppress(OSError):  # ffmpeg stopped reading early; its log says why
        for index, frame in enumerate(bars.frames(seconds, FPS)):
            stdin.write(frame)
            if index % FPS == 0:
                on_progress(index / total)
    with contextlib.suppress(OSError):
        stdin.close()
