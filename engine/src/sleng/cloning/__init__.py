"""
Purpose:  Voice cloning: a base voice speaks the Khmer, OpenVoice v2 swaps in a recorded timbre.
Layer:    sleng.cloning
Exports:  CloneKit, ClonedVoice, CloneStore, CloneDraft, ToneConverter, decode_clip
Depends:  sleng.audio, sleng.infra, sleng.domain; torch + librosa + OpenVoice (lazy)
Notes:    Pronunciation and rhythm stay the base voice's; only the timbre changes. Runs on CPU.
          OpenVoice's setup.py pins packages that do not build on Python 3.12, so install it with
          pip install --no-deps <OPENVOICE_URL in cloning/converter.py>
"""

from sleng.cloning.clip import CONVERTER_RATE, decode_clip, speech_seconds
from sleng.cloning.converter import ToneConverter
from sleng.cloning.store import CloneDraft, CloneStore
from sleng.cloning.voice import ClonedVoice, CloneKit

__all__ = [
    "CONVERTER_RATE",
    "CloneDraft",
    "CloneKit",
    "CloneStore",
    "ClonedVoice",
    "ToneConverter",
    "decode_clip",
    "speech_seconds",
]
