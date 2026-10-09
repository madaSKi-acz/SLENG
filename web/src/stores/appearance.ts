/**
 * Purpose: Light/dark/system mode, accent colour and interface language; applied to <html>.
 * Layer:   web/stores
 * Exports: useAppearanceStore, MODES, ACCENTS, Mode, Accent
 * Depends: pinia, i18n, lib/util
 * Notes:   index.html applies mode + accent before first paint with the same storage keys.
 */
import { defineStore } from 'pinia';

import { type Locale, i18n, initialLocale } from '@/i18n';
import { readStored, writeStored } from '@/lib/util';

export const MODES = ['system', 'light', 'dark'] as const;
export const ACCENTS = ['indigo', 'teal', 'graphite', 'plum'] as const;
export type Mode = (typeof MODES)[number];
export type Accent = (typeof ACCENTS)[number];

const DARK_QUERY = '(prefers-color-scheme: dark)';

function pick<T extends string>(value: string | null, allowed: readonly T[], fallback: T): T {
  return allowed.find((item) => item === value) ?? fallback;
}

export const useAppearanceStore = defineStore('appearance', {
  state: () => ({
    mode: pick(readStored('mode'), MODES, 'system'),
    accent: pick(readStored('palette'), ACCENTS, 'indigo'),
    locale: initialLocale(),
  }),
  actions: {
    setMode(mode: Mode): void {
      this.mode = mode;
      writeStored('mode', mode);
      this.apply();
    },
    setAccent(accent: Accent): void {
      this.accent = accent;
      writeStored('palette', accent);
      this.apply();
    },
    setLocale(locale: Locale): void {
      this.locale = locale;
      writeStored('lang', locale);
      this.apply();
    },
    apply(): void {
      const root = document.documentElement;
      const dark = window.matchMedia(DARK_QUERY).matches;
      root.dataset.mode = this.mode === 'system' ? (dark ? 'dark' : 'light') : this.mode;
      root.dataset.palette = this.accent;
      root.lang = this.locale;
      i18n.global.locale.value = this.locale;
      document.title = i18n.global.t('doc_title');
    },
    /** Follow the operating system when it switches between light and dark. */
    followSystem(): void {
      window.matchMedia(DARK_QUERY).addEventListener('change', () => this.apply());
    },
  },
});
