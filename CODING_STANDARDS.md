# SLENG coding standards

These are hard rules, not suggestions. Pre-commit enforces them on every commit:

```bash
pip install -e "engine[all,dev]" && pre-commit install   # once
pre-commit run --all-files                               # any time
```

## 1. Size limits

| Rule | Limit | Enforced by |
|---|---|---|
| File length | **≤ 300 lines** (aim for ≤ 200) | `tools/check_limits.py`, ESLint `max-lines` |
| Line length | **≤ 100 characters** | `tools/check_limits.py`, ruff, Prettier |
| Function length | **≤ 20 code lines** (blank lines, comments and the docstring do not count) | `tools/check_limits.py` (Python), ESLint `max-lines-per-function` |
| Parameters | ≤ 5 including `self` (Python), ≤ 4 (TypeScript) | ruff `PLR0913`, ESLint `max-params` |
| Cyclomatic complexity | ≤ 8 | ruff `C901`, ESLint `complexity` |
| Nesting depth | ≤ 3 | ESLint `max-depth` |

When a file passes 300 lines, split it **by responsibility**, never by cutting it in half.
The line-length limit exists so the line-count limit cannot be dodged by packing code sideways.

## 2. File header (every source file)

The header tells a person or an agent what the file is for without reading the body.

```python
"""
Purpose:  Split Khmer text into speakable chunks with the pause that follows each one.
Layer:    sleng.text (pure: no I/O, no state)
Exports:  split_text, chunks_from_lines
Depends:  sleng.domain, sleng.text.normalize, sleng.text.segment
Invariants: every chunk has non-empty spoken text.
"""
```

```ts
/**
 * Purpose: Typed calls to the engine HTTP API; the only place that knows URLs.
 * Layer:   web/api
 * Exports: engine
 * Depends: api/http, api/types
 */
```

```vue
<!--
  Purpose: One voice as a selectable card with its voiceprint.
  Layer:   web/components/voices
  Props:   voice, selected · Emits: select
-->
```

- **Purpose** and **Layer** are required (checked). **Exports** and **Depends** are expected.
- **Invariants / Notes** only when something is not obvious from the code.
- No "Used by" list: it goes stale. Find callers with search instead.

## 3. Architecture

```
engine/src/sleng/          Python engine (no UI knowledge)
  domain/     value objects, options, errors, voice catalog, VoiceEngine protocol   (pure)
  infra/      ffmpeg runner, LRU cache, optional-dependency loader
  text/       Khmer normalisation, numbers, splitting                               (pure)
  audio/      polish, loudness, timeline merge, resample, cleanup filters
  cloning/    clip decoding, OpenVoice converter, clone store, cloned voice
  media/      subtitles, ASS captions, video renderer, scenes, pop art
  voices/     concrete engines (MMS, Edge, fake), cache/cleanup decorators, registry
  services/   use cases: speech, exports, video, voices, background jobs
  container.py  composition root = the public Python API (`Sleng`)
  adapters/   http (FastAPI) and cli; translate in, call a service, translate out
web/src/                   Vue 3 + TypeScript UI (no engine logic)
  api/        the only code that talks HTTP
  stores/     Pinia stores: state + actions
  components/ rendering only; read stores, emit events
  lib/        framework-free helpers (player, clip queue, voiceprint, format)
  i18n/       English + Khmer messages
```

Import direction is one-way and checked by import-linter:
`adapters → container → services → voices → cloning | media → audio | text → infra → domain`.

## 4. Design rules

1. **Composition over inheritance.** Inherit only for a real "is-a" (a `StudioScene` *is* a
   `GlowScene` with voice bars). Roles are `Protocol`s (`VoiceEngine`).
2. **Decorators for cross-cutting behaviour**: `CachedVoice`, `CleanedVoice` wrap any engine.
3. **Value objects are frozen dataclasses.** `Audio` always carries its sample rate.
4. **No module-level mutable state.** Dependencies arrive through constructors; `Sleng` wires them.
5. **Pure transforms stay pure functions** (`number_to_khmer`). Do not wrap them in classes.
6. **Errors**: raise `SlengError` subclasses with a user-readable message. Adapters map them to
   exit codes or HTTP statuses. Never swallow an exception silently.
7. **Heavy libraries** (torch, transformers, librosa, edge-tts, OpenVoice) are imported lazily,
   through `sleng.infra.deps.require`, inside the class that needs them.
8. **Names are full words.** One-letter names only for loop indices, maths (`x`, `t`) and coordinates.
9. **Strict types.** `mypy --strict` for the engine, `strict` TypeScript with no `any` for the web.
10. **Web**: components never call `fetch`; stores never touch the DOM; every visible string goes
    through i18n and exists in both `en` and `km`.

## 5. Tests

- Engine: `pytest` in `engine/tests`. No network, no torch: build the engine with `Settings(fake=True)`.
- Web: Vitest, added per store/lib module as they stabilise.
