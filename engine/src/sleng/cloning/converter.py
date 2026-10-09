"""
Purpose:  OpenVoice v2 tone-colour converter: measure a speaker's timbre, convert speech to it.
Layer:    sleng.cloning
Exports:  ToneConverter, OPENVOICE_URL
Depends:  torch, huggingface_hub, openvoice (all lazy); sleng.cloning.clip
Notes:    Imports only openvoice.models/utils/mel_processing: openvoice.api pulls in text
          front-ends with old pins. First use downloads ~130 MB from myshell-ai/OpenVoiceV2.
"""

from __future__ import annotations

import logging
import sys
import threading
from typing import Any

import numpy as np

from sleng.cloning.clip import CONVERTER_RATE, voiced
from sleng.domain.audio import FloatSamples
from sleng.domain.errors import DependencyError
from sleng.infra.deps import require

log = logging.getLogger(__name__)
REPO = "myshell-ai/OpenVoiceV2"
OPENVOICE_URL = "https://github.com/myshell-ai/OpenVoice/archive/refs/heads/main.zip"
PIECE_SECONDS = 10
DEFAULT_TAU = 0.3


class ToneConverter:
    """Lazy-loaded converter shared by every cloned voice (one model, one lock)."""

    def __init__(self, device: str | None = None) -> None:
        self._device = device
        self._model: Any = None
        self._hps: Any = None
        self._lock = threading.Lock()

    def embed(self, wave: FloatSamples) -> Any:
        """Speaker embedding of float audio at CONVERTER_RATE, averaged over ~10 s pieces."""
        torch = require("torch")
        pieces = _pieces(voiced(wave))
        with self._lock, torch.no_grad():
            self._load()
            refs = [self._reference(piece) for piece in pieces]
        return torch.stack(refs).mean(0).cpu()

    def convert(self, wave: FloatSamples, source: Any, target: Any) -> FloatSamples:
        """Float audio spoken with timbre `source` -> the same speech with timbre `target`."""
        torch = require("torch")
        with self._lock, torch.no_grad():
            self._load()
            spec = self._spec(wave)
            lengths = torch.LongTensor([spec.size(-1)]).to(self._device)
            src, tgt = source.to(self._device), target.to(self._device)
            out = self._model.voice_conversion(
                spec, lengths, sid_src=src, sid_tgt=tgt, tau=DEFAULT_TAU
            )[0]
        return np.asarray(out[0, 0].cpu().float().numpy(), dtype=np.float32)

    def _reference(self, piece: FloatSamples) -> Any:
        return self._model.ref_enc(self._spec(piece).transpose(1, 2)).unsqueeze(-1)

    def _load(self) -> None:
        if self._model is not None:
            return
        torch = require("torch")
        hub = require("huggingface_hub", "huggingface-hub")
        self._device = self._device or ("cuda" if torch.cuda.is_available() else "cpu")
        log.info("Loading OpenVoice v2 converter on %s (first run downloads ~130 MB)", self._device)
        hps, model = _build_model(hub, self._device)
        state = _load_checkpoint(torch, hub.hf_hub_download(REPO, "converter/checkpoint.pth"))
        model.load_state_dict(state["model"], strict=False)
        self._hps, self._model = hps, model
        log.info("Converter ready")

    def _spec(self, wave: FloatSamples) -> Any:
        torch = require("torch")
        mel = require("openvoice.mel_processing", OPENVOICE_URL)
        data = self._hps.data
        samples = torch.from_numpy(np.ascontiguousarray(wave, dtype=np.float32))
        signal = samples.to(self._device).unsqueeze(0)
        sizes = (data.filter_length, data.sampling_rate, data.hop_length, data.win_length)
        return mel.spectrogram_torch(signal, *sizes, center=False)


def _pieces(wave: FloatSamples) -> list[FloatSamples]:
    step = PIECE_SECONDS * CONVERTER_RATE
    starts = [i for i in range(0, len(wave), step) if len(wave) - i > CONVERTER_RATE]
    return [wave[i : i + step] for i in starts] or [wave]


def _build_model(hub: Any, device: str) -> tuple[Any, Any]:
    utils, synthesizer = _import_openvoice()
    hps = utils.get_hparams_from_file(hub.hf_hub_download(REPO, "converter/config.json"))
    symbols = len(getattr(hps, "symbols", []))
    spec_channels = hps.data.filter_length // 2 + 1
    model = synthesizer(symbols, spec_channels, n_speakers=hps.data.n_speakers, **hps.model)
    return hps, model.to(device).eval()


def _import_openvoice() -> tuple[Any, Any]:
    try:
        from openvoice import utils
        from openvoice.models import SynthesizerTrn
    except ImportError as err:
        raise DependencyError(
            "Voice cloning needs OpenVoice. Install it with the Python that runs the engine: "
            f"{sys.executable} -m pip install --no-deps {OPENVOICE_URL}"
        ) from err
    return utils, SynthesizerTrn


def _load_checkpoint(torch: Any, path: str) -> Any:
    try:
        return torch.load(path, map_location="cpu", weights_only=True)
    # This checkpoint holds more than tensors.
    except Exception:  # noqa: BLE001
        return torch.load(path, map_location="cpu", weights_only=False)
