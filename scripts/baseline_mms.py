"""Synthesize Khmer speech with facebook/mms-tts-khm (baseline quality check).

Usage:
    python scripts/baseline_mms.py                       # uses data/prompts_km.txt
    python scripts/baseline_mms.py --text "សួស្តី"        # single sentence
    python scripts/baseline_mms.py --out outputs/mms --device cuda
"""
import argparse
from pathlib import Path

import scipy.io.wavfile as wavfile
import torch
from transformers import AutoTokenizer, VitsModel

MODEL_ID = "facebook/mms-tts-khm"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--text", help="Single sentence to synthesize")
    p.add_argument("--prompts", default="data/prompts_km.txt")
    p.add_argument("--out", default="outputs/mms")
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = p.parse_args()

    lines = [args.text] if args.text else [
        l.strip() for l in Path(args.prompts).read_text(encoding="utf-8").splitlines() if l.strip()
    ]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = VitsModel.from_pretrained(MODEL_ID).to(args.device).eval()
    rate = model.config.sampling_rate

    for i, line in enumerate(lines, 1):
        inputs = tokenizer(line, return_tensors="pt").to(args.device)
        with torch.no_grad():
            wav = model(**inputs).waveform[0].cpu().numpy()
        path = out / f"{i:03d}.wav"
        wavfile.write(path, rate, wav)
        print(f"[{i}/{len(lines)}] {path}  ({len(wav) / rate:.1f}s)  {line}")


if __name__ == "__main__":
    main()
