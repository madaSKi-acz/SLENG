"""
Purpose:  A cloned voice: speak with the base voice, then convert the result to the clone's timbre.
Layer:    sleng.cloning
Exports:  ClonedVoice, CloneKit
Depends:  sleng.cloning.{store, converter, timbre, clip}, sleng.audio, sleng.domain
"""

from __future__ import annotations

from typing import Any

from sleng.audio.polish import polish
from sleng.audio.resample import to_float_at
from sleng.cloning.clip import CONVERTER_RATE
from sleng.cloning.converter import ToneConverter
from sleng.cloning.store import CloneStore
from sleng.cloning.timbre import BaseTimbres
from sleng.domain.audio import Audio
from sleng.domain.voice import VoiceEngine, VoiceInfo

MIN_CONVERT_SAMPLES = CONVERTER_RATE // 10  # shorter audio (an empty line) keeps the base voice


class CloneKit:
    """Everything cloned voices share: the store, the converter and the base timbres."""

    def __init__(self, store: CloneStore, converter: ToneConverter) -> None:
        self.store = store
        self.converter = converter
        self.timbres = BaseTimbres(store, converter)

    def voice(self, info: VoiceInfo, base: VoiceEngine) -> ClonedVoice:
        """Engine for a saved clone, speaking through `base`."""
        return ClonedVoice(base, info.base_id, self.store.embedding(info.id), self)


class ClonedVoice:
    """VoiceEngine that converts its base voice's speech to a cloned timbre."""

    def __init__(self, base: VoiceEngine, base_id: str, target: Any, kit: CloneKit) -> None:
        self._base = base
        self._base_id = base_id
        self._target = target
        self._kit = kit

    def synthesize(self, text: str, speed: float = 1.0) -> Audio:
        wave = to_float_at(self._base.synthesize(text, speed), CONVERTER_RATE)
        if len(wave) > MIN_CONVERT_SAMPLES:
            source = self._kit.timbres.get(self._base_id, self._base)
            wave = self._kit.converter.convert(wave, source, self._target)
        return polish(Audio.from_float(wave, CONVERTER_RATE))
