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
**Download WAV** saves the full joined audio (with **Smart merge** on: loudness matched across chunks, short gaps where a long sentence was cut mid-way, crossfade for near-zero gaps; untick it for a plain join). **Chunks (.zip)** saves every chunk as its own WAV plus `chunks.txt`. Speed, pauses and chunk size are adjustable.
**Voices:** the UI offers Microsoft neural Khmer voices (Sreymom, Piseth; via `edge-tts`, needs internet,
much more natural) and the offline MMS-TTS model. Text is sent to Microsoft for the online voices; for
commercial use take the same voices from the official Azure Speech service.

**Cloned voices:** `🧬 Clone a voice…` under the Voice list makes a new voice from 10–30 s of one person
speaking (record in the browser or upload wav/mp3/m4a; any language). Pick **Woman** or **Man**, name it, save;
it appears under *Cloned voices* and works everywhere (Speak, WAV, MP4). How it works: the Khmer is spoken by a
base voice (Sreymom for a woman, Piseth for a man, or MMS offline) and the OpenVoice v2 tone-colour converter
(MIT) turns it into the cloned timbre, so pronunciation and rhythm stay the base voice's. Runs on CPU; the first
save downloads the converter (~130 MB). Clips are kept in `voices/` (git-ignored). Install once:

```bash
pip install --no-deps https://github.com/myshell-ai/OpenVoice/archive/refs/heads/main.zip
```

(`--no-deps` because its setup.py pins old packages that do not build on Python 3.12.) Only clone voices you
have permission to use.

**Noise cleanup** (ffmpeg filters, nothing extra to install; see `scripts/audio_fx.py`):
- *Clone recordings* are cleaned before cloning (rumble, hum, steady room noise and hiss removed, level evened).
  In the clone dialog, switch **Cleaned / Original** to hear both and choose which one is cloned.
- *Generated speech*: **Voice cleanup** in Delivery. **Light** (default) takes the hiss and rumble off, which mostly
  matters for cloned voices; **Studio** adds stronger denoise, less boom, more presence, a softer "s" and even
  volume; **Off** gives the raw voice. It applies to Speak, WAV, zip and MP4.
  Echo/reverb in a recording cannot be removed this way: record in a small, soft room for the best clone.

**Video / subtitles:** every line in the list under the player is editable (click the text and type;
the subtitle and the voice both follow your edit; click `3 ▶` to play from that line). **Export MP4** renders a black
screen with subtitles that follow the voice (HD, Full HD, vertical or square); **Subtitles (.srt)** exports the
timings for CapCut/Premiere/DaVinci. Subtitles keep your original digits (the voice reads them as words). The font is the bundled
**Kantumruy Pro** (`scripts/fonts/`, SIL OFL licence); use `--font path\to\font.ttf` to swap it. Video options: look (**Pop** = a cute, modern scene drawn by code for every video: pastel mesh gradient with
grain, Y2K rings/squiggles/dot grids, floating stickers - hearts, stars, smileys, daisies, clouds, planets - and
voice bars on a frosted-glass pill; palettes Candy, Mint, Sunset, Night neon; each export gets a design number you
can type into `Design #` to recreate it), other looks
(Studio = dark glowing gradient + voice bars + gradient progress bar, Glow only, Plain black), accent colour, optional title, and
word-by-word highlight of the spoken text. ffmpeg comes with the `imageio-ffmpeg` package.

**Language and theme:** the top bar switches the interface between English and Khmer (ខ្មែរ) and opens
**Appearance**: System / Light / Dark and an accent colour (Indigo, Teal, Graphite, Plum). Both are remembered.
Error messages that come from the server stay in English.

**Editor:** `⛶ Full screen` gives a distraction-free editor (Speak works from inside it), `A−/A+` change the text size,
`Find & replace` fixes spellings in bulk, `Ctrl+Enter` speaks, `Esc` stops. Drop a .txt file on the editor to load
it; select part of the text to speak only that part. With a title, the video opens on a title card.

Options: `--port 8000`, `--device cpu|cuda`, `--no-browser`. The first run downloads the model.

### Long text (command line)

```bash
python scripts/baseline_mms.py --file data/sample_long.txt   # -> outputs/mms/full.wav
python scripts/baseline_mms.py --file my_article.txt --chunks # also saves each chunk; add --plain-merge to disable smart merge
```

The text is cleaned, digits (១២៣ or 123) are spelled out as Khmer words, split at `។`
and over-long sentences at spaces (max 110 chars), synthesized chunk by chunk and joined
with pauses (`--pause`, `--para-pause`). Offline check of the splitter: `cd scripts && python test_khmer_text.py`.

## Open question

Do you want a specific voice (your own), or just any clear Khmer voice?
That decides between route 2 and route 3.

## Licences of what ends up in a video

- Pop backgrounds, stickers and bars: generated by this project's code (`scripts/pop_art.py`), no stock assets.
- Font: Kantumruy Pro, SIL Open Font License 1.1 (`scripts/fonts/OFL.txt`) - free to use in videos, including commercial.
- Voice: MMS-TTS is CC-BY-NC 4.0 (non-commercial). The `edge-tts` voices are an unofficial route to Microsoft's
  service; for monetised/commercial videos use the same voices via the official Azure Speech service.
