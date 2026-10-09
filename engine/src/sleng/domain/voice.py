"""
Purpose:  What a voice is (VoiceInfo), what it can do (VoiceEngine), and the built-in catalog.
Layer:    sleng.domain (pure)
Exports:  VoiceSource, Gender, VoiceInfo, VoiceEngine, SREYMOM, PISETH, MMS, BUILTIN_VOICES,
          DEFAULT_BASE, builtin_voice
Depends:  sleng.domain.audio
Invariants: this module is the only list of built-in voices; the UI reads it through the API.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from sleng.domain.audio import Audio


class VoiceSource(str, Enum):
    """Where the speech comes from."""

    ONLINE = "online"
    OFFLINE = "offline"
    CLONED = "cloned"


class Gender(str, Enum):
    """Voice gender as shown to the user (cloned voices pick their base voice by it)."""

    WOMAN = "woman"
    MAN = "man"


@dataclass(frozen=True)
class VoiceInfo:
    """Description of one voice. `base_id` is the built-in voice that does the actual speaking."""

    id: str
    name: str
    source: VoiceSource
    gender: Gender | None
    base_id: str
    max_chars: int = 250

    @property
    def cloned(self) -> bool:
        return self.source is VoiceSource.CLONED


class VoiceEngine(Protocol):
    """Anything that can read one line of Khmer aloud."""

    def synthesize(self, text: str, speed: float = 1.0) -> Audio:
        """Speech for `text` (already normalised) at the given speed (1.0 = normal)."""
        ...


SREYMOM = VoiceInfo(
    id="km-KH-SreymomNeural",
    name="Sreymom",
    source=VoiceSource.ONLINE,
    gender=Gender.WOMAN,
    base_id="km-KH-SreymomNeural",
)
PISETH = VoiceInfo(
    id="km-KH-PisethNeural",
    name="Piseth",
    source=VoiceSource.ONLINE,
    gender=Gender.MAN,
    base_id="km-KH-PisethNeural",
)
MMS = VoiceInfo(
    id="mms", name="MMS", source=VoiceSource.OFFLINE, gender=None, base_id="mms", max_chars=110
)
BUILTIN_VOICES: tuple[VoiceInfo, ...] = (SREYMOM, PISETH, MMS)
DEFAULT_BASE: dict[Gender, str] = {Gender.WOMAN: SREYMOM.id, Gender.MAN: PISETH.id}


def builtin_voice(voice_id: str) -> VoiceInfo | None:
    """The built-in voice with this id, or None."""
    return next((voice for voice in BUILTIN_VOICES if voice.id == voice_id), None)
