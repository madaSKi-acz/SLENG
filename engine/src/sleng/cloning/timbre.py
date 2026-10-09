"""
Purpose:  Timbre of each base voice (the "from" side of a conversion), measured once, kept on disk.
Layer:    sleng.cloning
Exports:  BaseTimbres, BASE_SENTENCES
Depends:  sleng.cloning.store, sleng.cloning.converter, sleng.audio.resample, torch (lazy)
"""

from __future__ import annotations

import threading
from typing import Any

from sleng.audio.resample import to_float_at
from sleng.cloning.clip import CONVERTER_RATE
from sleng.cloning.converter import ToneConverter
from sleng.cloning.store import CloneStore
from sleng.domain.audio import Audio, FloatSamples
from sleng.domain.voice import VoiceEngine
from sleng.infra.deps import require

# Each base voice reads these once so the converter can measure what it sounds like.
BASE_SENTENCES = (
    "សួស្តី! ខ្ញុំជាសំឡេងភាសាខ្មែរ។",
    "ថ្ងៃនេះអាកាសធាតុល្អណាស់។",
    "សូមអរគុណច្រើនសម្រាប់ជំនួយរបស់អ្នក។",
    "ព្រះរាជាណាចក្រកម្ពុជា ជាប្រទេសមួយនៅអាស៊ីអាគ្នេយ៍។",
    "តើអ្នកសុខសប្បាយជាទេ?",
    "ខ្ញុំចូលចិត្តញ៉ាំបាយជាមួយគ្រួសារ។",
    "ភ្នំពេញ គឺជារាជធានីនៃប្រទេសកម្ពុជា។",
    "សូមស្វាគមន៍មកកាន់កម្មវិធីរបស់យើង។",
)


class BaseTimbres:
    """Memoised base-voice embeddings, cached in memory and in <voices>/_base/<id>.pt."""

    def __init__(self, store: CloneStore, converter: ToneConverter) -> None:
        self._store = store
        self._converter = converter
        self._memo: dict[str, Any] = {}
        self._lock = threading.Lock()

    def get(self, base_id: str, base: VoiceEngine) -> Any:
        with self._lock:
            if base_id not in self._memo:
                self._memo[base_id] = self._load_or_measure(base_id, base)
            return self._memo[base_id]

    def _load_or_measure(self, base_id: str, base: VoiceEngine) -> Any:
        torch = require("torch")
        path = self._store.base_timbre_path(base_id)
        if path.is_file():
            return torch.load(path, map_location="cpu", weights_only=True)
        embedding = self._converter.embed(_reading(base))
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(embedding, path)
        return embedding


def _reading(base: VoiceEngine) -> FloatSamples:
    joined = Audio.join([base.synthesize(sentence) for sentence in BASE_SENTENCES])
    return to_float_at(joined, CONVERTER_RATE)
