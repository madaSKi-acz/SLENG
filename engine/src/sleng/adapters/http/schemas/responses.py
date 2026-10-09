"""
Purpose:  Response bodies of the HTTP API, each built from a domain object.
Layer:    sleng.adapters.http.schemas
Exports:  ChunkOut, VoiceOut, JobOut, HealthOut, OptionsOut, PaletteOut, SizeOut, ErrorOut
Depends:  pydantic, sleng.domain, sleng.services.jobs
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from sleng.domain import Chunk, CleanupLevel, Gender, PauseKind, VideoTheme, VoiceInfo, VoiceSource
from sleng.services.jobs import JobStatus, JobView


class ErrorOut(BaseModel):
    """Every error response has this shape."""

    error: str
    type: str


class ChunkOut(BaseModel):
    """One line: what is shown, what is read, and the pause after it."""

    text: str
    spoken: str
    pause: PauseKind

    @classmethod
    def from_domain(cls, chunk: Chunk) -> ChunkOut:
        return cls(text=chunk.display, spoken=chunk.spoken, pause=chunk.pause)


class VoiceOut(BaseModel):
    """A voice the UI can offer."""

    id: str
    name: str
    source: VoiceSource
    gender: Gender | None
    base_id: str
    cloned: bool
    max_chars: int

    @classmethod
    def from_domain(cls, info: VoiceInfo) -> VoiceOut:
        return cls(
            id=info.id,
            name=info.name,
            source=info.source,
            gender=info.gender,
            base_id=info.base_id,
            cloned=info.cloned,
            max_chars=info.max_chars,
        )


class JobOut(BaseModel):
    """Snapshot of a background job."""

    id: str
    kind: str
    status: JobStatus
    progress: float
    error: str | None
    meta: dict[str, Any]
    created: float

    @classmethod
    def from_view(cls, view: JobView) -> JobOut:
        return cls(
            id=view.id,
            kind=view.kind,
            status=view.status,
            progress=view.progress,
            error=view.error,
            meta=view.meta,
            created=view.created,
        )


class HealthOut(BaseModel):
    """Liveness and version."""

    status: str
    version: str
    fake: bool


class PaletteOut(BaseModel):
    """A video palette and its group ("pop" or "other")."""

    name: str
    group: str


class SizeOut(BaseModel):
    """A supported video frame size."""

    width: int
    height: int


class OptionsOut(BaseModel):
    """Choices the UI offers, so it never hard-codes engine knowledge."""

    themes: list[VideoTheme]
    palettes: list[PaletteOut]
    sizes: list[SizeOut]
    cleanup_levels: list[CleanupLevel]
