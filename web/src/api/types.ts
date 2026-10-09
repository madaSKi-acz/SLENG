/**
 * Purpose: Types of the engine HTTP API (mirror of engine/src/sleng/adapters/http/schemas).
 * Layer:   web/api
 * Exports: request/response types used by api/engine.ts and the stores
 * Notes:   `npm run gen:api` writes the generated schema to src/api/schema.d.ts for comparison.
 */
export type PauseKind = 'phrase' | 'sentence' | 'paragraph';
export type CleanupLevel = 'off' | 'light' | 'studio';
export type VideoTheme = 'plain' | 'glow' | 'studio' | 'pop';
export type VoiceSource = 'online' | 'offline' | 'cloned';
export type Gender = 'woman' | 'man';
export type JobStatus = 'queued' | 'running' | 'done' | 'failed';
export type ExportKind = 'wav' | 'zip' | 'srt';

export interface Voice {
  id: string;
  name: string;
  source: VoiceSource;
  gender: Gender | null;
  base_id: string;
  cloned: boolean;
  max_chars: number;
}

export interface Chunk {
  text: string;
  spoken: string;
  pause: PauseKind;
}

export interface SpeechOptions {
  voice: string;
  speed: number;
  cleanup: CleanupLevel;
}

export interface PauseOptions {
  sentence: number;
  paragraph: number;
  smart: boolean;
}

export interface ScriptLine {
  text: string;
  pause: PauseKind;
}

export interface Script {
  text?: string;
  lines?: ScriptLine[];
  max_chars?: number;
}

export interface Narration {
  script: Script;
  speech: SpeechOptions;
  pauses: PauseOptions;
}

export interface LineRequest {
  text: string;
  pause: PauseKind;
  speech: SpeechOptions;
  pauses: PauseOptions;
}

export interface LineAudio {
  blob: Blob;
  gapAfter: number;
}

export interface VideoOptions {
  width: number;
  height: number;
  theme: VideoTheme;
  palette: string;
  title: string;
  title_card: boolean;
  subtitles: boolean;
  karaoke: boolean;
  progress_bar: boolean;
  seed: number | null;
}

export interface VideoJob extends Narration {
  video: VideoOptions;
}

export interface Job {
  id: string;
  kind: string;
  status: JobStatus;
  progress: number;
  error: string | null;
  meta: Record<string, unknown>;
  created: number;
}

export interface Palette {
  name: string;
  group: 'pop' | 'other';
}

export interface FrameSize {
  width: number;
  height: number;
}

export interface EngineOptions {
  themes: VideoTheme[];
  palettes: Palette[];
  sizes: FrameSize[];
  cleanup_levels: CleanupLevel[];
}

export interface CloneForm {
  name: string;
  gender: Gender;
  baseId: string;
  clean: boolean;
  clip: Blob;
}
