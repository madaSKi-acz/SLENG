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

### Web UI (local, with audio player)

```bash
pip install -r requirements.txt
python scripts/app.py          # opens http://127.0.0.1:7860
```

Paste or open a `.txt` file, press **Speak**. Long text is split automatically and playback
starts as soon as the first chunk is ready; click any chunk to replay from there, and
**Download WAV** saves the full joined audio. Speed, pauses and chunk size are adjustable.
**Voices:** the UI offers Microsoft neural Khmer voices (Sreymom, Piseth; via `edge-tts`, needs internet,
much more natural) and the offline MMS-TTS model. Text is sent to Microsoft for the online voices; for
commercial use take the same voices from the official Azure Speech service.

Options: `--port 8000`, `--device cpu|cuda`, `--no-browser`. The first run downloads the model.

### Long text (command line)

```bash
python scripts/baseline_mms.py --file data/sample_long.txt   # -> outputs/mms/full.wav
python scripts/baseline_mms.py --file my_article.txt --chunks # also saves each chunk
```

The text is cleaned, digits (១២៣ or 123) are spelled out as Khmer words, split at `។`
and over-long sentences at spaces (max 110 chars), synthesized chunk by chunk and joined
with pauses (`--pause`, `--para-pause`). Offline check of the splitter: `cd scripts && python test_khmer_text.py`.

## Open question

Do you want a specific voice (your own), or just any clear Khmer voice?
That decides between route 2 and route 3.
