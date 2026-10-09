"""
Purpose:  Saved clones on disk: <root>/<10-hex id>/{ref.wav, se.pt, meta.json} plus base timbres.
Layer:    sleng.cloning
Exports:  CloneStore, CloneDraft, CLONE_PREFIX
Depends:  sleng.domain, torch (lazy), scipy
Invariants: voice ids are "clone:<10 hex>"; folders starting with "_" are not clones.
            The format matches clones saved before the refactor, so they keep working.
"""

from __future__ import annotations

import json
import re
import shutil
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import scipy.io.wavfile as wavfile

from sleng.cloning.clip import CONVERTER_RATE
from sleng.domain.audio import Audio, FloatSamples
from sleng.domain.errors import NotFoundError
from sleng.domain.voice import MMS, Gender, VoiceInfo, VoiceSource, builtin_voice
from sleng.infra.deps import require

CLONE_PREFIX = "clone:"
META_FILE = "meta.json"
EMBEDDING_FILE = "se.pt"
REFERENCE_FILE = "ref.wav"
_CLONE_ID = re.compile(r"clone:([0-9a-f]{10})")


@dataclass(frozen=True)
class CloneDraft:
    """Everything about a new clone except its audio and embedding."""

    name: str
    gender: Gender
    base_id: str
    seconds: float
    cleaned: bool

    def meta(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "gender": self.gender.value,
            "base": self.base_id,
            "seconds": self.seconds,
            "cleaned": self.cleaned,
            "created": time.time(),
        }


class CloneStore:
    """File-system store of cloned voices."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def voices(self) -> list[VoiceInfo]:
        """Every saved clone, oldest first."""
        if not self._root.is_dir():
            return []
        found = [self._read(folder) for folder in self._root.iterdir() if _is_clone(folder)]
        return [info for _, info in sorted(found, key=lambda pair: pair[0])]

    def get(self, voice_id: str) -> VoiceInfo:
        folder = self._folder(voice_id)
        if not _is_clone(folder):
            raise NotFoundError(f"Unknown voice: {voice_id}")
        return self._read(folder)[1]

    def save(self, draft: CloneDraft, clip: FloatSamples, embedding: Any) -> VoiceInfo:
        torch = require("torch")
        folder = self._root / uuid.uuid4().hex[:10]
        folder.mkdir(parents=True)
        reference = Audio.from_float(clip, CONVERTER_RATE)
        wavfile.write(folder / REFERENCE_FILE, reference.rate, reference.samples)
        torch.save(embedding, folder / EMBEDDING_FILE)
        meta = json.dumps(draft.meta(), ensure_ascii=False, indent=1)
        (folder / META_FILE).write_text(meta, encoding="utf-8")
        return self._read(folder)[1]

    def delete(self, voice_id: str) -> None:
        """Remove a clone; deleting one that is already gone is not an error."""
        folder = self._folder(voice_id)
        if folder.is_dir():
            shutil.rmtree(folder)

    def embedding(self, voice_id: str) -> Any:
        torch = require("torch")
        path = self._folder(voice_id) / EMBEDDING_FILE
        return torch.load(path, map_location="cpu", weights_only=True)

    def base_timbre_path(self, base_id: str) -> Path:
        return self._root / "_base" / f"{base_id}.pt"

    def _folder(self, voice_id: str) -> Path:
        match = _CLONE_ID.fullmatch(voice_id)
        if not match:
            raise NotFoundError(f"Unknown voice: {voice_id}")
        return self._root / match.group(1)

    @staticmethod
    def _read(folder: Path) -> tuple[float, VoiceInfo]:
        meta = json.loads((folder / META_FILE).read_text(encoding="utf-8"))
        base = builtin_voice(str(meta.get("base", ""))) or MMS
        info = VoiceInfo(
            id=CLONE_PREFIX + folder.name,
            name=str(meta["name"]),
            source=VoiceSource.CLONED,
            gender=Gender(meta["gender"]),
            base_id=base.id,
            max_chars=base.max_chars,
        )
        return float(meta.get("created", 0)), info


def _is_clone(folder: Path) -> bool:
    has_files = (folder / META_FILE).is_file() and (folder / EMBEDDING_FILE).is_file()
    return not folder.name.startswith("_") and has_files
