"""
Purpose:  Audio and subtitle exports: one WAV, a zip with a WAV per line, an SRT file.
Layer:    sleng.services
Exports:  ExportService
Depends:  sleng.services.speech, sleng.audio.wav, sleng.media.subtitles
"""

from __future__ import annotations

import io
import zipfile

from sleng.audio.wav import encode_wav
from sleng.domain.chunk import Script
from sleng.domain.options import SpeechOptions
from sleng.domain.requests import NarrationRequest
from sleng.media.subtitles import DEFAULT_CUE_CHARS, make_cues, to_srt
from sleng.services.speech import SpeechService


class ExportService:
    """File exports built on SpeechService."""

    def __init__(self, speech: SpeechService) -> None:
        self._speech = speech

    def wav(self, request: NarrationRequest) -> bytes:
        """The whole narration as one WAV file."""
        return encode_wav(self._speech.narrate(request).timeline.audio)

    def zip(self, script: Script, speech: SpeechOptions) -> bytes:
        """001.wav, 002.wav... one per line, plus chunks.txt listing their text."""
        chunks = self._speech.chunks(script)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for number, chunk in enumerate(chunks, 1):
                audio = self._speech.speak_chunk(chunk, speech)
                archive.writestr(f"{number:03d}.wav", encode_wav(audio))
            listing = (f"{number:03d}\t{chunk.display}" for number, chunk in enumerate(chunks, 1))
            archive.writestr("chunks.txt", "\n".join(listing))
        return buffer.getvalue()

    def srt(self, request: NarrationRequest, max_chars: int = DEFAULT_CUE_CHARS) -> str:
        """Subtitles timed to the narration (for CapCut, Premiere, DaVinci)."""
        narration = self._speech.narrate(request)
        displays = [chunk.display for chunk in narration.chunks]
        return to_srt(make_cues(displays, narration.timeline.spans, max_chars))
