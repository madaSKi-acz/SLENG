/**
 * Purpose: Downloads: whole WAV, per-line zip, SRT, and MP4 (a background job with progress).
 * Layer:   web/stores
 * Exports: useExportsStore
 * Depends: pinia, api/engine, lib/util, stores/{script, settings, status}
 */
import { defineStore } from 'pinia';

import { engine } from '@/api/engine';
import type { ExportKind, Narration, VideoOptions } from '@/api/types';
import { saveBlob, sleep } from '@/lib/util';
import { useScriptStore } from '@/stores/script';
import { useSettingsStore } from '@/stores/settings';
import { type Message, useStatusStore } from '@/stores/status';

type Busy = '' | ExportKind | 'mp4';

const FILES: Record<ExportKind, string> = {
  wav: 'khmer-tts.wav',
  zip: 'khmer-tts-lines.zip',
  srt: 'khmer-tts.srt',
};
const BUSY_KEYS: Record<ExportKind, string> = {
  wav: 'm_build_wav',
  zip: 'm_pack',
  srt: 'm_build_srt',
};
const VIDEO_FILE = 'khmer-tts.mp4';
const POLL_MS = 800;

async function narration(): Promise<Narration> {
  const script = useScriptStore();
  await script.ensureLines();
  const { speech, pauses } = useSettingsStore();
  return { script: script.exportScript, speech, pauses };
}

function videoOptions(): VideoOptions {
  const video = useSettingsStore().video;
  const [width = 1280, height = 720] = video.size.split('x').map(Number);
  const seed = Number.parseInt(video.seed, 10);
  return {
    width,
    height,
    theme: video.theme,
    palette: video.palette,
    title: video.title.trim(),
    title_card: video.titleCard,
    subtitles: video.subtitles,
    karaoke: video.karaoke,
    progress_bar: video.progressBar,
    seed: seed > 0 ? seed : null,
  };
}

export const useExportsStore = defineStore('exports', {
  state: () => ({ busy: '' as Busy }),
  actions: {
    async download(kind: ExportKind): Promise<void> {
      await this.track(kind, BUSY_KEYS[kind], async () => {
        saveBlob(await engine.exportFile(kind, await narration()), FILES[kind]);
        return { key: 'm_saved_file', vars: { file: FILES[kind] } };
      });
    },
    async video(): Promise<void> {
      await this.track('mp4', 'm_render', async () => {
        const job = await engine.startVideo({ ...(await narration()), video: videoOptions() });
        await this.waitFor(job.id);
        const { blob, seed } = await engine.jobResult(job.id);
        saveBlob(blob, VIDEO_FILE);
        return { key: 'm_saved_video', vars: { file: VIDEO_FILE, seed: seed ?? '?' } };
      });
    },
    async waitFor(id: string): Promise<void> {
      const status = useStatusStore();
      let job = await engine.job(id);
      while (job.status === 'queued' || job.status === 'running') {
        status.show('m_render', { p: Math.round(job.progress * 100) });
        status.progress = job.progress;
        await sleep(POLL_MS);
        job = await engine.job(id);
      }
      if (job.status === 'failed') throw new Error(job.error ?? 'Video render failed.');
    },
    async track(kind: Busy, busyKey: string, work: () => Promise<Message>): Promise<void> {
      if (this.busy) return;
      const status = useStatusStore();
      this.busy = kind;
      status.show(busyKey, { p: 0 });
      try {
        const done = await work();
        status.set(done);
        status.toast(done);
      } catch (error) {
        status.fail(error);
      } finally {
        this.busy = '';
        status.progress = 0;
      }
    },
  },
});
