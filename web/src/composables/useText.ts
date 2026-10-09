/**
 * Purpose: Translation helpers for components: t(), Message rendering, durations.
 * Layer:   web/composables
 * Exports: useText
 * Depends: vue-i18n, stores/status (Message)
 */
import { useI18n } from 'vue-i18n';

import type { Message } from '@/stores/status';

export function useText() {
  const { t } = useI18n();
  const render = (message: Message): string =>
    'key' in message ? t(message.key, message.vars ?? {}) : message.text;
  const duration = (seconds: number): string => {
    const rounded = Math.round(seconds);
    if (rounded < 60) return t('dur_sec', { s: rounded });
    return t('dur_min', { m: Math.floor(rounded / 60), s: rounded % 60 });
  };
  return { t, render, duration };
}
