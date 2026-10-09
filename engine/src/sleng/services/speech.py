"""
Purpose:  Speech use cases: split a script, speak one line, narrate a whole script.
Layer:    sleng.services
Exports:  SpeechService, Narration, Progress
Depends:  sleng.voices.VoiceRegistry, sleng.text, sleng.audio.timeline, sleng.domain
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sleng.audio.timeline import merge
from sleng.domain.audio import Audio, Timeline
from sleng.domain.chunk import Chunk, Script
from sleng.domain.errors import InvalidInputError
from sleng.domain.options import SpeechOptions
from sleng.domain.requests import NarrationRequest
from sleng.domain.voice import VoiceEngine
from sleng.text import chunks_from_lines, normalize, split_text
from sleng.voices.registry import VoiceRegistry

Progress = Callable[[float], None]


def ignore_progress(_: float) -> None:
    return None


@dataclass(frozen=True, eq=False)
class Narration:
    """A narrated script: its chunks and the merged audio with each chunk's time span."""

    chunks: tuple[Chunk, ...]
    timeline: Timeline


class SpeechService:
    """Turns text into speech with the registry's voices."""

    def __init__(self, voices: VoiceRegistry) -> None:
        self._voices = voices

    def split(self, text: str, max_chars: int) -> list[Chunk]:
        return split_text(text, max_chars)

    def chunks(self, script: Script) -> list[Chunk]:
        """Edited lines win over raw text; raises InvalidInputError when nothing is readable."""
        if script.lines:
            chunks = chunks_from_lines(script.lines)
        else:
            chunks = split_text(script.text, script.max_chars)
        if not chunks:
            raise InvalidInputError("No readable text.")
        return chunks

    def speak_line(self, text: str, speech: SpeechOptions) -> Audio:
        """One line as the user wrote it (numbers are spelled out here)."""
        spoken = normalize(text)
        if not spoken:
            raise InvalidInputError("This line has no readable text.")
        return self._engine(speech).synthesize(spoken, speech.speed)

    def speak_chunk(self, chunk: Chunk, speech: SpeechOptions) -> Audio:
        return self._engine(speech).synthesize(chunk.spoken, speech.speed)

    def narrate(
        self, request: NarrationRequest, on_progress: Progress = ignore_progress
    ) -> Narration:
        """Synthesize every chunk in order and merge them with the requested pauses."""
        chunks = self.chunks(request.script)
        engine = self._engine(request.speech)
        parts = []
        for index, chunk in enumerate(chunks, 1):
            audio = engine.synthesize(chunk.spoken, request.speech.speed)
            parts.append((audio, request.pauses.gap_after(chunk.pause)))
            on_progress(index / len(chunks))
        return Narration(tuple(chunks), merge(parts, smart=request.pauses.smart))

    def _engine(self, speech: SpeechOptions) -> VoiceEngine:
        return self._voices.engine(speech.voice, speech.cleanup)
