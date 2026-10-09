/**
 * Purpose: Every user setting (voice, delivery, export, editor size), saved between visits.
 * Layer:   web/stores
 * Exports: useSettingsStore, SettingsState, VideoSettings
 * Depends: pinia, lib/util (storage), api/types
 * Notes:   main.ts subscribes persist() to every change.
 */
import { defineStore } from 'pinia';

import type { CleanupLevel, PauseOptions, SpeechOptions, VideoTheme } from '@/api/types';
import { readJson, writeStored } from '@/lib/util';

export interface VideoSettings {
  size: string;
  theme: VideoTheme;
  palette: string;
  title: string;
  seed: string;
  subtitles: boolean;
  karaoke: boolean;
  progressBar: boolean;
  titleCard: boolean;
}

export interface SettingsState {
  voice: string;
  speed: number;
  sentencePause: number;
  paragraphPause: number;
  maxChars: number;
  smart: boolean;
  cleanup: CleanupLevel;
  exportTab: 'audio' | 'video';
  editorScale: number;
  video: VideoSettings;
}

const STORAGE_KEY = 'settings';
const DEFAULT_VIDEO: VideoSettings = {
  size: '1280x720',
  theme: 'pop',
  palette: 'candy',
  title: '',
  seed: '',
  subtitles: true,
  karaoke: true,
  progressBar: true,
  titleCard: true,
};
const DEFAULTS: SettingsState = {
  voice: 'km-KH-SreymomNeural',
  speed: 1,
  sentencePause: 0.2,
  paragraphPause: 0.6,
  maxChars: 250,
  smart: true,
  cleanup: 'light',
  exportTab: 'audio',
  editorScale: 1.15,
  video: DEFAULT_VIDEO,
};

function load(): SettingsState {
  const saved = readJson(STORAGE_KEY, DEFAULTS);
  return { ...DEFAULTS, ...saved, video: { ...DEFAULT_VIDEO, ...saved.video } };
}

export const useSettingsStore = defineStore('settings', {
  state: load,
  getters: {
    speech: (state): SpeechOptions => ({
      voice: state.voice,
      speed: state.speed,
      cleanup: state.cleanup,
    }),
    pauses: (state): PauseOptions => ({
      sentence: state.sentencePause,
      paragraph: state.paragraphPause,
      smart: state.smart,
    }),
  },
  actions: {
    persist(): void {
      writeStored(STORAGE_KEY, JSON.stringify(this.$state));
    },
  },
});
