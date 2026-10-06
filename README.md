# SLENG – Khmer text-to-speech

Experiments for a clear Khmer TTS voice. Three routes, in order of effort:

| Route | When to use | Hardware |
|---|---|---|
| 1. `facebook/mms-tts-khm` baseline | Hear baseline quality first (~5 min) | CPU is fine |
| 2. Fish Speech + LoRA (Kaggle notebook) | You want a *specific* voice (e.g. your own) | Kaggle/Colab GPU |
| 3. Train Piper or VITS on DDD-Cambodia | Lighter or commercially usable model | ~8–12 GB VRAM or free Colab/Kaggle |

Note: MMS-TTS is CC-BY-NC 4.0 (non-commercial). Check the licence of any dataset
and model before commercial use.

## 1. Baseline

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/baseline_mms.py                 # synthesizes data/prompts_km.txt -> outputs/mms/*.wav
python scripts/baseline_mms.py --text "សួស្តី"  # one sentence
```

Needs access to `huggingface.co` to download the model (~140 MB).

## Open question

Do you want a specific voice (your own), or just any clear Khmer voice?
That decides between route 2 and route 3.
