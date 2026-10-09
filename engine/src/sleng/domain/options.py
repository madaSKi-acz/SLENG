"""
Purpose:  Options a caller can set: voice/speed/cleanup, pauses, and video look.
Layer:    sleng.domain (pure)
Exports:  CleanupLevel, VideoTheme, VIDEO_SIZES, SpeechOptions, PauseOptions, VideoOptions
Depends:  sleng.domain.chunk, sleng.domain.errors
Invariants: PauseOptions.gap_after is the single source of the pause rule (the UI asks for it).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from sleng.domain.chunk import PauseKind
from sleng.domain.errors import InvalidInputError

VIDEO_SIZES: tuple[tuple[int, int], ...] = ((1280, 720), (1920, 1080), (1080, 1920), (1080, 1080))
SHORT_PHRASE_GAP = 0.1


class CleanupLevel(str, Enum):
    """Noise cleanup applied to generated speech."""

    OFF = "off"
    LIGHT = "light"
    STUDIO = "studio"


class VideoTheme(str, Enum):
    """Look of an exported video."""

    PLAIN = "plain"
    GLOW = "glow"
    STUDIO = "studio"
    POP = "pop"


@dataclass(frozen=True)
class SpeechOptions:
    """Which voice reads, how fast, and how much the result is cleaned up."""

    voice: str = "km-KH-SreymomNeural"
    speed: float = 1.0
    cleanup: CleanupLevel = CleanupLevel.LIGHT


@dataclass(frozen=True)
class PauseOptions:
    """Silences between chunks. Smart mode also evens loudness and keeps phrase cuts short."""

    sentence: float = 0.2
    paragraph: float = 0.6
    smart: bool = True

    def gap_after(self, kind: PauseKind) -> float:
        """Seconds of silence after a chunk of this kind."""
        if kind is PauseKind.PARAGRAPH:
            return self.paragraph
        if kind is PauseKind.PHRASE and self.smart:
            return min(self.sentence, SHORT_PHRASE_GAP)
        return self.sentence


@dataclass(frozen=True)
class VideoOptions:
    """Size, look and caption settings of an MP4 export."""

    width: int = 1280
    height: int = 720
    theme: VideoTheme = VideoTheme.STUDIO
    palette: str = "gemini"
    title: str = ""
    intro_seconds: float = 2.6
    subtitles: bool = True
    karaoke: bool = True
    progress_bar: bool = True
    seed: int | None = None
    subtitle_chars: int = 60
    font_scale: float = 0.075

    def __post_init__(self) -> None:
        if (self.width, self.height) not in VIDEO_SIZES:
            raise InvalidInputError(f"Unsupported video size {self.width}x{self.height}.")

    @property
    def intro(self) -> float:
        """Title-card length in seconds; zero when there is no title."""
        return self.intro_seconds if self.title.strip() else 0.0
