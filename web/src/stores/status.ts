/**
 * Purpose: The status line, its progress bar, and toasts, all kept as translatable messages.
 * Layer:   web/stores
 * Exports: useStatusStore, Message, Toast, messageOf
 * Depends: pinia, api/http (ApiError), lib/util (UserError)
 */
import { defineStore } from 'pinia';

import { ApiError } from '@/api/http';
import { UserError } from '@/lib/util';

/** An i18n key with variables, or raw text (engine error messages stay English). */
export type Message = { key: string; vars?: Record<string, unknown> } | { text: string };

export interface Toast {
  id: number;
  message: Message;
  error: boolean;
}

const TOAST_MS = 3000;
const ERROR_TOAST_MS = 6000;

export function messageOf(error: unknown): Message {
  if (error instanceof UserError) return { key: error.key };
  if (error instanceof ApiError && error.offline) return { key: 'm_offline' };
  return { text: error instanceof Error ? error.message : String(error) };
}

export const useStatusStore = defineStore('status', {
  state: () => ({
    message: { key: 'm_ready' } as Message,
    error: false,
    progress: 0,
    toasts: [] as Toast[],
    toastCount: 0,
  }),
  actions: {
    show(key: string, vars: Record<string, unknown> = {}): void {
      this.set({ key, vars });
    },
    set(message: Message): void {
      this.message = message;
      this.error = false;
    },
    fail(error: unknown): void {
      const message = messageOf(error);
      this.message = message;
      this.error = true;
      this.toast(message, true);
    },
    toast(message: Message, error = false): void {
      this.toastCount += 1;
      const id = this.toastCount;
      this.toasts.push({ id, message, error });
      window.setTimeout(() => this.dismiss(id), error ? ERROR_TOAST_MS : TOAST_MS);
    },
    dismiss(id: number): void {
      this.toasts = this.toasts.filter((toast) => toast.id !== id);
    },
  },
});
