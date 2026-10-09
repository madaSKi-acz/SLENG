"""
Purpose:  The engine's public vocabulary: value objects, options, requests, errors, voice catalog.
Layer:    sleng.domain (pure: numpy and the standard library only)
Exports:  everything a caller needs to build a request and read a result
Depends:  sleng.domain.*
"""

from sleng.domain.audio import Audio, Span, Timeline
from sleng.domain.chunk import Chunk, PauseKind, Script, ScriptLine
from sleng.domain.errors import (
    ConflictError,
    DependencyError,
    ExternalServiceError,
    InvalidInputError,
    NotFoundError,
    SlengError,
)
from sleng.domain.options import (
    VIDEO_SIZES,
    CleanupLevel,
    PauseOptions,
    SpeechOptions,
    VideoOptions,
    VideoTheme,
)
from sleng.domain.requests import NarrationRequest, VideoRequest
from sleng.domain.voice import (
    BUILTIN_VOICES,
    DEFAULT_BASE,
    MMS,
    PISETH,
    SREYMOM,
    Gender,
    VoiceEngine,
    VoiceInfo,
    VoiceSource,
    builtin_voice,
)

__all__ = [
    "BUILTIN_VOICES",
    "DEFAULT_BASE",
    "MMS",
    "PISETH",
    "SREYMOM",
    "VIDEO_SIZES",
    "Audio",
    "Chunk",
    "CleanupLevel",
    "ConflictError",
    "DependencyError",
    "ExternalServiceError",
    "Gender",
    "InvalidInputError",
    "NarrationRequest",
    "NotFoundError",
    "PauseKind",
    "PauseOptions",
    "Script",
    "ScriptLine",
    "SlengError",
    "Span",
    "SpeechOptions",
    "Timeline",
    "VideoOptions",
    "VideoRequest",
    "VideoTheme",
    "VoiceEngine",
    "VoiceInfo",
    "VoiceSource",
    "builtin_voice",
]
