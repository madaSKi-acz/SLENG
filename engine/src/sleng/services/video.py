"""
Purpose:  Video use case: narrate a script, build captions, render the MP4.
Layer:    sleng.services
Exports:  VideoService, NARRATION_SHARE
Depends:  sleng.services.speech, sleng.media.{renderer, ass, subtitles, palettes, fonts}
"""

from __future__ import annotations

import secrets
from pathlib import Path

from sleng.domain.audio import Timeline
from sleng.domain.chunk import Chunk
from sleng.domain.options import VideoOptions, VideoTheme
from sleng.domain.requests import VideoRequest
from sleng.media.ass import DEFAULT_LOOK, POP_LOOK, AssDocument, CaptionLayout
from sleng.media.fonts import FontSet
from sleng.media.palettes import accent, resolve_palette
from sleng.media.renderer import RenderJob, VideoRenderer
from sleng.media.subtitles import make_cues
from sleng.services.speech import Progress, SpeechService, ignore_progress

NARRATION_SHARE = 0.4  # progress: first 40% is synthesis, the rest is encoding
MAX_SEED = 99_999


class VideoService:
    """Renders narrated videos; returns the design seed so a look can be recreated."""

    def __init__(self, speech: SpeechService, renderer: VideoRenderer, fonts: FontSet) -> None:
        self._speech = speech
        self._renderer = renderer
        self._fonts = fonts

    def render(
        self, request: VideoRequest, out_path: Path, on_progress: Progress = ignore_progress
    ) -> int:
        """Write the MP4 to `out_path` and return the seed used for its design."""
        video = request.video
        seed = video.seed or secrets.randbelow(MAX_SEED) + 1  # a design number, not security
        narration = self._speech.narrate(
            request.narration, lambda done: on_progress(done * NARRATION_SHARE)
        )
        timeline = narration.timeline.shifted(video.intro) if video.intro else narration.timeline
        palette = resolve_palette(video.theme, video.palette)
        captions = self._captions(narration.chunks, timeline, video, palette)
        job = RenderJob(timeline.audio, captions, video, palette, seed)
        self._renderer.render(job, out_path, lambda done: on_progress(_encode_share(done)))
        return seed

    def _captions(
        self, chunks: tuple[Chunk, ...], timeline: Timeline, video: VideoOptions, palette: str
    ) -> str | None:
        if not video.subtitles:
            return None
        displays = [chunk.display for chunk in chunks]
        cues = make_cues(displays, timeline.spans, video.subtitle_chars)
        font_size = int(min(video.width, video.height) * video.font_scale)
        layout = CaptionLayout(
            video.width, video.height, self._fonts.family, font_size, accent(palette)
        )
        look = POP_LOOK if video.theme is VideoTheme.POP else DEFAULT_LOOK
        document = AssDocument(layout, look, video.karaoke)
        return document.render(cues, video.title, timeline.audio.duration, video.intro)


def _encode_share(done: float) -> float:
    """Encoding progress (0..1) mapped onto the part of the bar after narration."""
    return NARRATION_SHARE + done * (1 - NARRATION_SHARE)
