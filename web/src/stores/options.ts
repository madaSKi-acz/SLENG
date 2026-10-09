/**
 * Purpose: Picker choices served by the engine (video themes, palettes, sizes, cleanup levels).
 * Layer:   web/stores
 * Exports: useOptionsStore
 * Depends: pinia, api/engine
 * Notes:   The UI never hard-codes these; it shows what the engine supports.
 */
import { defineStore } from 'pinia';

import { engine } from '@/api/engine';
import type { EngineOptions } from '@/api/types';

export const useOptionsStore = defineStore('options', {
  state: (): EngineOptions => ({ themes: [], palettes: [], sizes: [], cleanup_levels: [] }),
  actions: {
    async load(): Promise<void> {
      try {
        this.$patch(await engine.options());
      } catch {
        // Offline: the voices load reports it; pickers stay empty until the engine is back.
      }
    },
  },
});
