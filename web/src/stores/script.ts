/**
 * Purpose: The script text and the lines it was split into (each line editable, with a state).
 * Layer:   web/stores
 * Exports: useScriptStore, Line, LineState
 * Depends: pinia, api/engine, stores/settings, lib/util
 */
import { defineStore } from 'pinia';

import { engine } from '@/api/engine';
import type { Chunk, PauseKind, Script } from '@/api/types';
import { UserError, readStored, writeStored } from '@/lib/util';
import { useSettingsStore } from '@/stores/settings';

export type LineState = 'waiting' | 'gen' | 'ready' | 'edited';

export interface Line {
  text: string;
  pause: PauseKind;
  state: LineState;
}

const toLine = (chunk: Chunk): Line => ({ text: chunk.text, pause: chunk.pause, state: 'waiting' });

export const useScriptStore = defineStore('script', {
  state: () => ({
    text: readStored('text') ?? '',
    lines: [] as Line[],
    splitFrom: null as string | null, // the text the lines came from (null = a selection)
    splitId: 0, // bumps on every split so line rows re-render
    selection: '',
  }),
  getters: {
    /** What exports send: the (edited) lines once split, else the raw text. */
    exportScript(state): Script {
      if (state.lines.length) {
        return { lines: state.lines.map(({ text, pause }) => ({ text, pause })) };
      }
      return { text: state.text, max_chars: useSettingsStore().maxChars };
    },
  },
  actions: {
    setText(text: string): void {
      this.text = text;
      writeStored('text', text);
    },
    async split(only?: string): Promise<void> {
      const source = only ?? this.text;
      if (!source.trim()) throw new UserError('m_enter_text');
      const chunks = await engine.split(source, useSettingsStore().maxChars);
      if (!chunks.length) throw new UserError('m_no_text');
      this.lines = chunks.map(toLine);
      this.splitFrom = only === undefined ? this.text : null;
      this.splitId += 1;
    },
    /** Split again only when the text changed since the last split. */
    async ensureLines(): Promise<void> {
      if (!this.lines.length || this.splitFrom !== this.text) await this.split();
    },
    editLine(index: number, text: string): void {
      const line = this.lines[index];
      if (!line) return;
      line.text = text;
      line.state = 'edited';
    },
    markLine(index: number, state: LineState): void {
      const line = this.lines[index];
      if (line) line.state = state;
    },
    resetStates(): void {
      for (const line of this.lines) line.state = 'waiting';
    },
  },
});
