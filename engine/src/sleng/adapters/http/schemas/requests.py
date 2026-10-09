"""
Purpose:  Request bodies of the HTTP API, with size limits, each converting itself to the domain.
Layer:    sleng.adapters.http.schemas
Exports:  SpeechIn, PausesIn, LineIn, ScriptIn, NarrationIn, SplitIn, LineSpeechIn, VideoIn,
          VideoJobIn, MAX_TEXT_CHARS, MAX_LINE_CHARS, MAX_LINES
Depends:  pydantic, sleng.domain
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sleng.domain import (
    SREYMOM,
    VIDEO_SIZES,
    CleanupLevel,
    NarrationRequest,
    PauseKind,
    PauseOptions,
    Script,
    ScriptLine,
    SpeechOptions,
    VideoOptions,
    VideoRequest,
    VideoTheme,
)

MAX_TEXT_CHARS = 200_000
MAX_LINE_CHARS = 2_000
MAX_LINES = 5_000
TITLE_CARD_SECONDS = 2.6


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SpeechIn(_Strict):
    """Which voice reads, how fast, and how much the result is cleaned."""

    voice: str = Field(default=SREYMOM.id, max_length=64)
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    cleanup: CleanupLevel = CleanupLevel.LIGHT

    def to_domain(self) -> SpeechOptions:
        return SpeechOptions(voice=self.voice, speed=self.speed, cleanup=self.cleanup)


class PausesIn(_Strict):
    """Silence between sentences and paragraphs; smart = even loudness, short phrase gaps."""

    sentence: float = Field(default=0.2, ge=0, le=5)
    paragraph: float = Field(default=0.6, ge=0, le=10)
    smart: bool = True

    def to_domain(self) -> PauseOptions:
        return PauseOptions(sentence=self.sentence, paragraph=self.paragraph, smart=self.smart)


class LineIn(_Strict):
    """One line as shown to (and maybe edited by) the user."""

    text: str = Field(max_length=MAX_LINE_CHARS)
    pause: PauseKind = PauseKind.SENTENCE


class ScriptIn(_Strict):
    """Raw text to split, or lines already split (lines win when given)."""

    text: str = Field(default="", max_length=MAX_TEXT_CHARS)
    lines: list[LineIn] = Field(default_factory=list, max_length=MAX_LINES)
    max_chars: int = Field(default=250, ge=20, le=1000)

    def to_domain(self) -> Script:
        lines = tuple(ScriptLine(line.text, line.pause) for line in self.lines)
        return Script(text=self.text, lines=lines, max_chars=self.max_chars)


class NarrationIn(_Strict):
    """A script read by one voice with the given pauses."""

    script: ScriptIn
    speech: SpeechIn = Field(default_factory=SpeechIn)
    pauses: PausesIn = Field(default_factory=PausesIn)

    def to_domain(self) -> NarrationRequest:
        return NarrationRequest(
            self.script.to_domain(), self.speech.to_domain(), self.pauses.to_domain()
        )


class SplitIn(_Strict):
    """Text to split into lines."""

    text: str = Field(max_length=MAX_TEXT_CHARS)
    max_chars: int = Field(default=250, ge=20, le=1000)


class LineSpeechIn(_Strict):
    """One line to speak, plus what follows it (for the X-Gap-After header)."""

    text: str = Field(min_length=1, max_length=MAX_LINE_CHARS)
    speech: SpeechIn = Field(default_factory=SpeechIn)
    pause: PauseKind = PauseKind.SENTENCE
    pauses: PausesIn = Field(default_factory=PausesIn)


class VideoIn(_Strict):
    """Size, look and captions of an MP4 export."""

    width: int = 1280
    height: int = 720
    theme: VideoTheme = VideoTheme.STUDIO
    palette: str = Field(default="gemini", max_length=32)
    title: str = Field(default="", max_length=120)
    title_card: bool = True
    subtitles: bool = True
    karaoke: bool = True
    progress_bar: bool = True
    seed: int | None = Field(default=None, ge=1, le=99_999)

    @model_validator(mode="after")
    def _known_size(self) -> VideoIn:
        if (self.width, self.height) not in VIDEO_SIZES:
            raise ValueError(f"unsupported size {self.width}x{self.height}")
        return self

    def to_domain(self) -> VideoOptions:
        return VideoOptions(
            width=self.width,
            height=self.height,
            theme=self.theme,
            palette=self.palette,
            title=self.title,
            intro_seconds=TITLE_CARD_SECONDS if self.title_card else 0.0,
            subtitles=self.subtitles,
            karaoke=self.karaoke,
            progress_bar=self.progress_bar,
            seed=self.seed,
        )


class VideoJobIn(NarrationIn):
    """A narration rendered as an MP4 in the background."""

    video: VideoIn = Field(default_factory=VideoIn)

    def to_video_request(self) -> VideoRequest:
        return VideoRequest(self.to_domain(), self.video.to_domain())
