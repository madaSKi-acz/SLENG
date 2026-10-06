"""Synthesize Khmer speech with facebook/mms-tts-khm.

Long text is cleaned, numbers are spelled out in Khmer, and the text is split
into short chunks that are synthesized one by one and joined into one WAV.

Usage:
    python scripts/baseline_mms.py --file article.txt          # long text -> outputs/mms/full.wav
    python scripts/baseline_mms.py --text "សួស្តី"               # short text
    python scripts/baseline_mms.py                              # uses data/prompts_km.txt
    python scripts/baseline_mms.py --file article.txt --chunks  # also keep each chunk as a WAV
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import scipy.io.wavfile as wavfile
import torch
from transformers import AutoTokenizer, VitsModel

sys.path.insert(0, str(Path(__file__).parent))
from khmer_text import split_chunks  # noqa: E402

MODEL_ID = "facebook/mms-tts-khm"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--text", help="Text to synthesize (any length)")
    p.add_argument("--file", help="UTF-8 text file to synthesize (any length)")
    p.add_argument("--prompts", default="data/prompts_km.txt", help="Default input if no --text/--file")
    p.add_argument("--out", default="outputs/mms")
    p.add_argument("--name", default="full", help="Output file name (without .wav)")
    p.add_argument("--max-chars", type=int, default=110, help="Max characters per chunk")
    p.add_argument("--pause", type=float, default=0.2, help="Seconds of silence between sentences")
    p.add_argument("--para-pause", type=float, default=0.6, help="Seconds of silence between paragraphs")
    p.add_argument("--chunks", action="store_true", help="Also save every chunk as its own WAV")
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = p.parse_args()

    if args.text:
        raw = args.text
    else:
        raw = Path(args.file or args.prompts).read_text(encoding="utf-8")
    chunks = split_chunks(raw, args.max_chars)
    if not chunks:
        sys.exit("No text to synthesize.")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = VitsModel.from_pretrained(MODEL_ID).to(args.device).eval()
    rate = model.config.sampling_rate

    pieces = []
    for i, (text, pause_kind) in enumerate(chunks, 1):
        inputs = tokenizer(text, return_tensors="pt").to(args.device)
        if inputs["input_ids"].numel() == 0:
            continue
        with torch.no_grad():
            wav = model(**inputs).waveform[0].cpu().numpy()
        print(f"[{i}/{len(chunks)}] {len(wav) / rate:4.1f}s  {text}")
        if args.chunks:
            wavfile.write(out / f"{args.name}_{i:03d}.wav", rate, wav)
        pieces.append(wav)
        gap = args.para_pause if pause_kind == "paragraph" else args.pause
        pieces.append(np.zeros(int(gap * rate), dtype=wav.dtype))

    full = np.concatenate(pieces)
    path = out / f"{args.name}.wav"
    wavfile.write(path, rate, full)
    print(f"\nSaved {path}  ({len(full) / rate:.1f}s, {len(chunks)} chunks)")


if __name__ == "__main__":
    main()
