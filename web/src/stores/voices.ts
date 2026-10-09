/**
 * Purpose: The voice list from the engine, the selected voice, cloning and deleting voices.
 * Layer:   web/stores
 * Exports: useVoicesStore
 * Depends: pinia, api/engine, stores/{settings, status}
 */
import { defineStore } from 'pinia';

import { engine } from '@/api/engine';
import type { CloneForm, Gender, Voice } from '@/api/types';
import { useSettingsStore } from '@/stores/settings';
import { useStatusStore } from '@/stores/status';

export const useVoicesStore = defineStore('voices', {
  state: () => ({ list: [] as Voice[] }),
  getters: {
    selected(state): Voice | undefined {
      const id = useSettingsStore().voice;
      return state.list.find((voice) => voice.id === id);
    },
    builtin: (state): Voice[] => state.list.filter((voice) => !voice.cloned),
    cloned: (state): Voice[] => state.list.filter((voice) => voice.cloned),
  },
  actions: {
    /** Reload the list; keep the current voice if it still exists, else pick `prefer`/first. */
    async load(prefer?: string): Promise<void> {
      try {
        this.list = await engine.voices();
      } catch (error) {
        useStatusStore().fail(error);
        return;
      }
      const wanted = prefer ?? useSettingsStore().voice;
      const voice = this.list.find((item) => item.id === wanted) ?? this.list[0];
      if (voice && voice.id !== useSettingsStore().voice) this.select(voice);
    },
    /** Choosing a voice also resets the line length to what suits it. */
    select(voice: Voice): void {
      const settings = useSettingsStore();
      settings.voice = voice.id;
      settings.maxChars = voice.max_chars;
    },
    async clone(form: CloneForm): Promise<Voice> {
      const voice = await engine.cloneVoice(form);
      await this.load(voice.id);
      return voice;
    },
    async remove(voice: Voice): Promise<void> {
      await engine.deleteVoice(voice.id);
      await this.load(this.builtin[0]?.id);
    },
    /** The clip as it would be cloned (cleaned by the engine), to listen before saving. */
    previewClip(clip: Blob): Promise<Blob> {
      return engine.previewClip(clip, true);
    },
    /** The built-in voice that speaks for a clone of this gender. */
    baseFor(gender: Gender): string | undefined {
      return this.builtin.find((voice) => voice.gender === gender)?.id;
    },
  },
});
