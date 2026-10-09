/**
 * Purpose: Small framework-free helpers: storage, downloads, timing, text statistics, errors.
 * Layer:   web/lib (framework-free)
 * Exports: readStored, writeStored, readJson, saveBlob, sleep, speechSeconds, lineCount, UserError
 */
const STORAGE_PREFIX = 'sleng.';
const CHARS_PER_SECOND = 13; // rough Khmer reading speed, for the "about N of speech" hint

/** An error whose message is an i18n key (shown translated). */
export class UserError extends Error {
  constructor(readonly key: string) {
    super(key);
    this.name = 'UserError';
  }
}

export function readStored(key: string): string | null {
  try {
    return localStorage.getItem(STORAGE_PREFIX + key);
  } catch {
    return null;
  }
}

export function writeStored(key: string, value: string): void {
  try {
    localStorage.setItem(STORAGE_PREFIX + key, value);
  } catch {
    // Storage blocked (private mode): settings simply do not persist.
  }
}

export function readJson<T extends object>(key: string, fallback: T): Partial<T> {
  try {
    const parsed: unknown = JSON.parse(readStored(key) ?? '{}');
    return typeof parsed === 'object' && parsed !== null ? (parsed as Partial<T>) : {};
  } catch {
    return {};
  }
}

export function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 10_000);
}

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export function speechSeconds(text: string): number {
  return text.replace(/\s/g, '').length / CHARS_PER_SECOND;
}

export function lineCount(text: string): number {
  return text.split('\n').filter((line) => line.trim()).length;
}
