/**
 * Purpose: Speak the script line by line: synthesis runs ahead while playback follows.
 * Layer:   web/stores
 * Exports: usePlaybackStore
 * Depends: pinia, api/engine, lib/{clipQueue, linePlayer, util}, stores/{script, settings, status}
 * Notes:   Every run has a token; stop() or a new run bumps it and stale work quietly ends.
 */
import { defineStore } from 'pinia';
import { type Raw, markRaw } from 'vue';

import { engine } from '@/api/engine';
import type { LineAudio } from '@/api/types';
import { ClipQueue } from '@/lib/clipQueue';
import { LinePlayer } from '@/lib/linePlayer';
import { sleep } from '@/lib/util';
import { useScriptStore } from '@/stores/script';
import { useSettingsStore } from '@/stores/settings';
import { useStatusStore } from '@/stores/status';

type Queue = ClipQueue<LineAudio>;

interface PlaybackState {
  run: number;
  busy: boolean;
  current: number;
  playing: boolean;
  queue: Raw<Queue>;
  player: Raw<LinePlayer> | null;
}

export const usePlaybackStore = defineStore('playback', {
  state: (): PlaybackState => ({
    run: 0,
    busy: false,
    current: -1,
    playing: false,
    queue: markRaw(new ClipQueue<LineAudio>()),
    player: null,
  }),
  actions: {
    /** Speak from line `from` (0 = the whole script, or only the selected text). */
    async speak(from = 0): Promise<void> {
      const token = this.begin();
      const queue = this.queue;
      try {
        await this.prepare(from);
        this.produce(token, from, queue).catch((error: unknown) => this.abort(token, error));
        if (await this.consume(token, from, queue)) this.finish();
      } catch (error) {
        this.abort(token, error);
      } finally {
        if (token === this.run) this.busy = false;
      }
    },
    stop(): void {
      this.halt();
      useStatusStore().show('m_stopped');
    },
    toggle(): void {
      this.ensurePlayer().toggle();
    },
    begin(): number {
      this.halt();
      this.queue = markRaw(new ClipQueue<LineAudio>());
      this.busy = true;
      const status = useStatusStore();
      status.show('m_split');
      status.progress = 0;
      return this.run;
    },
    halt(): void {
      this.run += 1;
      this.queue.close();
      this.ensurePlayer().stop();
      this.busy = false;
      this.current = -1;
    },
    async prepare(from: number): Promise<void> {
      const script = useScriptStore();
      const selection = script.selection.trim();
      if (from === 0 && selection.length > 1) {
        await script.split(selection);
        useStatusStore().toast({ key: 'm_sel_only' });
      } else {
        await script.ensureLines();
      }
      script.resetStates();
    },
    async produce(token: number, from: number, queue: Queue): Promise<void> {
      const script = useScriptStore();
      const settings = useSettingsStore();
      const total = script.lines.length;
      for (let index = from; index < total && token === this.run; index++) {
        const line = script.lines[index];
        if (!line) return;
        script.markLine(index, 'gen');
        const { speech, pauses } = settings;
        const request = { text: line.text, pause: line.pause, speech, pauses };
        queue.put(index, await engine.speakLine(request));
        script.markLine(index, 'ready');
        this.report(index - from + 1, total - from);
      }
    },
    async consume(token: number, from: number, queue: Queue): Promise<boolean> {
      const total = useScriptStore().lines.length;
      for (let index = from; index < total; index++) {
        const clip = await queue.take(index);
        if (!clip || token !== this.run) return false;
        this.current = index;
        await this.ensurePlayer().play(clip.blob);
        if (token !== this.run) return false;
        if (index < total - 1) await sleep(clip.gapAfter * 1000);
      }
      return true;
    },
    report(done: number, total: number): void {
      const status = useStatusStore();
      status.show('m_gen', { n: done, total });
      status.progress = done / total;
    },
    finish(): void {
      this.current = -1;
      useStatusStore().show('m_finished');
    },
    abort(token: number, error: unknown): void {
      if (token !== this.run) return;
      this.halt();
      useStatusStore().fail(error);
    },
    ensurePlayer(): Raw<LinePlayer> {
      if (!this.player) {
        this.player = markRaw(new LinePlayer((playing) => (this.playing = playing)));
      }
      return this.player;
    },
  },
});
