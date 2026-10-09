"""
Purpose:  Voice use cases: list voices, preview a clip, save a cloned voice, delete one.
Layer:    sleng.services
Exports:  VoiceService, CloneRequest, MAX_NAME_CHARS
Depends:  sleng.voices.VoiceRegistry, sleng.cloning, sleng.audio.wav, sleng.domain
"""

from __future__ import annotations

from dataclasses import dataclass

from sleng.audio.wav import encode_wav
from sleng.cloning.clip import CONVERTER_RATE, MIN_SPEECH_SECONDS, decode_clip, speech_seconds
from sleng.cloning.store import CloneDraft
from sleng.cloning.voice import CloneKit
from sleng.domain.audio import Audio
from sleng.domain.errors import InvalidInputError
from sleng.domain.voice import DEFAULT_BASE, Gender, VoiceInfo, builtin_voice
from sleng.infra.ffmpeg import Ffmpeg
from sleng.voices.registry import VoiceRegistry

MAX_NAME_CHARS = 40


@dataclass(frozen=True)
class CloneRequest:
    """A new clone: who it is, the clip, and which built-in voice speaks for it."""

    name: str
    gender: Gender
    audio: bytes
    base_id: str | None = None  # None = the default base voice for the gender
    clean: bool = True  # clean the clip (room noise, hum) before measuring the timbre


class VoiceService:
    """Voice catalog and cloning."""

    def __init__(self, registry: VoiceRegistry, clones: CloneKit, ffmpeg: Ffmpeg) -> None:
        self._registry = registry
        self._clones = clones
        self._ffmpeg = ffmpeg

    def voices(self) -> list[VoiceInfo]:
        return self._registry.voices()

    def preview(self, audio: bytes, clean: bool) -> bytes:
        """The clip exactly as it would be cloned, as WAV (to listen before saving)."""
        wave = decode_clip(audio, self._ffmpeg, clean)
        return encode_wav(Audio.from_float(wave, CONVERTER_RATE))

    def clone(self, request: CloneRequest) -> VoiceInfo:
        """Measure the clip's timbre and save it as a new voice. First use downloads ~130 MB."""
        name = " ".join(request.name.split())[:MAX_NAME_CHARS]
        if not name:
            raise InvalidInputError("Give the voice a name.")
        base = _base_voice(request)
        clip = decode_clip(request.audio, self._ffmpeg, request.clean)
        seconds = speech_seconds(clip)
        if seconds < MIN_SPEECH_SECONDS:
            raise InvalidInputError(
                f"Only {seconds:.1f} s of speech found. "
                f"Use at least {MIN_SPEECH_SECONDS} s (10-30 s works best)."
            )
        embedding = self._clones.converter.embed(clip)
        draft = CloneDraft(name, request.gender, base.id, round(seconds, 1), request.clean)
        return self._clones.store.save(draft, clip, embedding)

    def delete(self, voice_id: str) -> None:
        self._clones.store.delete(voice_id)
        self._registry.forget(voice_id)


def _base_voice(request: CloneRequest) -> VoiceInfo:
    base = builtin_voice(request.base_id or DEFAULT_BASE[request.gender])
    if base is None:
        raise InvalidInputError("Pick one of the built-in voices as the base voice.")
    return base
