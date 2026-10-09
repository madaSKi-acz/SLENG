/**
 * Purpose: English + Khmer interface text (vue-i18n). km must have every key en has (typed).
 * Layer:   web/i18n
 * Exports: i18n, Locale, LOCALES, MessageKey, initialLocale
 * Depends: vue-i18n, en.json, km.json
 * Notes:   Messages are JSON data, so the code limits do not apply to their line length.
 *          Error messages that come from the engine stay in English.
 */
import { createI18n } from 'vue-i18n';

import en from '@/i18n/en.json';
import km from '@/i18n/km.json';
import { readStored } from '@/lib/util';

export type MessageSchema = typeof en;
export type MessageKey = keyof MessageSchema;
export type Locale = 'en' | 'km';
export const LOCALES: readonly Locale[] = ['en', 'km'];

const khmer: MessageSchema = km;

export function initialLocale(): Locale {
  const saved = readStored('lang');
  if (saved === 'en' || saved === 'km') return saved;
  return navigator.language.startsWith('km') ? 'km' : 'en';
}

export const i18n = createI18n<[MessageSchema], Locale, false>({
  legacy: false,
  locale: initialLocale(),
  fallbackLocale: 'en',
  messages: { en, km: khmer },
});
