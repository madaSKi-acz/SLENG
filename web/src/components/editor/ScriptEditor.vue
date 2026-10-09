<!--
  Purpose: The script editor: textarea with file drop, paste/clear, size, full screen, Speak/Stop.
  Layer:   web/components/editor
  Depends: stores/{script, settings, playback, status, ui}, EditorToolbar, FindReplace
  Notes:   Selecting part of the text makes Speak read only that part.
-->
<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';

import EditorToolbar from '@/components/editor/EditorToolbar.vue';
import FindReplace from '@/components/editor/FindReplace.vue';
import Icon from '@/components/ui/Icon.vue';
import { useText } from '@/composables/useText';
import { UserError, lineCount, speechSeconds } from '@/lib/util';
import { usePlaybackStore } from '@/stores/playback';
import { useScriptStore } from '@/stores/script';
import { useSettingsStore } from '@/stores/settings';
import { useStatusStore } from '@/stores/status';
import { useUiStore } from '@/stores/ui';

const MIN_SCALE = 0.9;
const MAX_SCALE = 2.6;

const script = useScriptStore();
const settings = useSettingsStore();
const playback = usePlaybackStore();
const status = useStatusStore();
const ui = useUiStore();
const { t, render, duration } = useText();
const area = ref<HTMLTextAreaElement | null>(null);
const findOpen = ref(false);
const dropping = ref(false);

const text = computed({ get: () => script.text, set: (value: string) => script.setText(value) });
const count = computed(() => {
  const summary = t('count', { c: script.text.length, l: lineCount(script.text) });
  const seconds = speechSeconds(script.text);
  return seconds ? summary + t('approx', { d: duration(seconds) }) : summary;
});

function trackSelection(): void {
  const el = area.value;
  if (el) script.selection = el.value.slice(el.selectionStart, el.selectionEnd);
}

async function loadFile(file: File): Promise<void> {
  script.setText(await file.text());
  status.toast({ key: 'm_loaded', vars: { file: file.name } });
}

async function paste(): Promise<void> {
  const el = area.value;
  if (!el) return;
  try {
    const clip = await navigator.clipboard.readText();
    el.setRangeText(clip, el.selectionStart, el.selectionEnd, 'end');
    script.setText(el.value);
  } catch {
    status.fail(new UserError('m_clip_blocked'));
    el.focus();
  }
}

function clear(): void {
  if (script.text && !window.confirm(t('m_clear_confirm'))) return;
  script.setText('');
  area.value?.focus();
}

function scale(step: number): void {
  const next = Number((settings.editorScale + step).toFixed(2));
  settings.editorScale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, next));
}

async function setFull(on: boolean): Promise<void> {
  ui.editorFull = on;
  document.body.style.overflow = on ? 'hidden' : '';
  try {
    if (on) await document.documentElement.requestFullscreen();
    else if (document.fullscreenElement) await document.exitFullscreen();
  } catch {
    // Browser full screen refused: the in-page full-screen editor still works.
  }
  await nextTick();
  if (on) area.value?.focus();
}

function onFullscreenChange(): void {
  if (!document.fullscreenElement && ui.editorFull) void setFull(false);
}

function onDrop(event: DragEvent): void {
  dropping.value = false;
  const files = Array.from(event.dataTransfer?.files ?? []);
  const file = files.find((f) => /\.txt$/i.test(f.name) || f.type.startsWith('text/'));
  if (!file) return;
  event.preventDefault();
  void loadFile(file);
}

onMounted(() => document.addEventListener('fullscreenchange', onFullscreenChange));
onBeforeUnmount(() => document.removeEventListener('fullscreenchange', onFullscreenChange));
</script>

<template>
  <section class="panel" :aria-label="t('script')">
    <div
      class="editor"
      :class="{ full: ui.editorFull }"
      :style="{ '--efs': `${settings.editorScale}rem` }"
      @keydown.esc="ui.editorFull && setFull(false)"
    >
      <EditorToolbar
        :full="ui.editorFull"
        @open="loadFile"
        @paste="paste"
        @clear="clear"
        @find="findOpen = !findOpen"
        @scale="scale"
        @full="setFull(!ui.editorFull)"
      />
      <FindReplace v-if="findOpen" />
      <textarea
        ref="area"
        v-model="text"
        spellcheck="false"
        :class="{ drop: dropping }"
        :aria-label="t('script')"
        :placeholder="t('placeholder')"
        @select="trackSelection"
        @keyup="trackSelection"
        @mouseup="trackSelection"
        @input="trackSelection"
        @dragenter.prevent="dropping = true"
        @dragover.prevent="dropping = true"
        @dragleave="dropping = false"
        @drop="onDrop"
      />
      <div class="foot">
        <button class="primary speak" :disabled="playback.busy" @click="playback.speak()">
          <Icon name="play" /><span>{{ t('speak') }}</span><kbd>Ctrl ↵</kbd>
        </button>
        <button :disabled="!playback.busy" @click="playback.stop()">
          <Icon name="stop" /><span>{{ t('stop') }}</span>
        </button>
        <span class="count">{{ count }}</span>
        <span class="grow" />
        <span v-if="ui.editorFull" class="hint" :class="{ 'err-text': status.error }">
          {{ render(status.message) }}
        </span>
        <span class="hint">{{ t('select_hint') }}</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
textarea {
  display: block;
  width: 100%;
  min-height: 42vh;
  resize: vertical;
  padding: 14px 16px;
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  background: var(--sunk);
  color: var(--ink);
  font: inherit;
  font-size: var(--efs);
  line-height: 1.9;
  tab-size: 2;
  transition: background 0.15s, border-color 0.15s;
}

textarea:focus {
  outline: none;
  border-color: var(--accent);
  background: var(--surface);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

textarea::placeholder {
  color: var(--mute);
}

textarea.drop {
  outline: 2px dashed var(--accent);
  outline-offset: -4px;
  background: var(--accent-soft);
}

.foot {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  align-items: center;
  margin-top: 12px;
}

.speak {
  padding: 8px 16px;
  font-size: 0.875rem;
}

.count {
  color: var(--mute);
  font-size: 0.78rem;
  font-variant-numeric: tabular-nums;
}

.full {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: var(--bg);
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.full > * {
  width: 100%;
  max-width: 1040px;
  margin-left: auto;
  margin-right: auto;
}

.full textarea {
  flex: 1;
  min-height: 0;
  resize: none;
}
</style>
