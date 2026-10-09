"""
Purpose:  Composite requests passed to the services (what to read + how + optional video look).
Layer:    sleng.domain (pure)
Exports:  NarrationRequest, VideoRequest
Depends:  sleng.domain.chunk, sleng.domain.options
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sleng.domain.chunk import Script
from sleng.domain.options import PauseOptions, SpeechOptions, VideoOptions


@dataclass(frozen=True)
class NarrationRequest:
    """A whole script read by one voice with the given pauses."""

    script: Script
    speech: SpeechOptions = field(default_factory=SpeechOptions)
    pauses: PauseOptions = field(default_factory=PauseOptions)


@dataclass(frozen=True)
class VideoRequest:
    """A narration rendered as an MP4."""

    narration: NarrationRequest
    video: VideoOptions = field(default_factory=VideoOptions)
