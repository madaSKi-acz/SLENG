<!--
  Purpose: One spoken line: its number (play from here), editable text, and synthesis state.
  Layer:   web/components/lines
  Props:   index, line, playing · Emits: play(index), edit(index, text)
  Notes:   The text is rendered once (not bound) so typing never moves the caret.
-->
<script setup lang="ts">
import { ref, watch } from 'vue';

import { useText } from '@/composables/useText';
import type { Line } from '@/stores/script';

const props = defineProps<{ index: number; line: Line; playing: boolean }>();
const emit = defineEmits<{ play: [index: number]; edit: [index: number, text: string] }>();
const { t } = useText();
const row = ref<HTMLLIElement | null>(null);
const initialText = props.line.text;

function onInput(event: Event): void {
  emit('edit', props.index, (event.target as HTMLElement).textContent ?? '');
}

watch(
  () => props.playing,
  (playing) => playing && row.value?.scrollIntoView({ block: 'nearest' }),
);
</script>

<template>
  <li ref="row" :class="[line.state, { playing }]">
    <button class="n" :title="t('play_from')" @click="emit('play', index)">{{ index + 1 }}</button>
    <span class="t" contenteditable="plaintext-only" spellcheck="false" @input="onInput">{{
      initialText
    }}</span>
    <span class="s">{{ t(`st_${line.state}`) }}</span>
  </li>
</template>

<style scoped>
li {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 6px 8px;
  border-radius: var(--r-sm);
  font-size: 0.9375rem;
  line-height: 1.8;
  border-left: 2px solid transparent;
  scroll-margin: 100px;
}

li:hover {
  background: var(--sunk);
}

li.playing {
  background: var(--accent-soft);
  border-left-color: var(--accent);
}

.n {
  gap: 4px;
  color: var(--mute);
  min-width: 2.6em;
  font-size: 0.78rem;
  font-variant-numeric: tabular-nums;
  border: 0;
  background: none;
  padding: 0 4px;
  user-select: none;
}

.n::after {
  content: '';
  border-left: 5px solid currentcolor;
  border-top: 4px solid transparent;
  border-bottom: 4px solid transparent;
  opacity: 0;
}

li:hover .n::after,
li.playing .n::after {
  opacity: 1;
}

.n:hover {
  color: var(--accent);
}

.t {
  flex: 1;
  outline: none;
  border-radius: 4px;
  padding: 0 4px;
}

.t:focus {
  background: var(--surface);
  box-shadow: 0 0 0 1px var(--accent);
}

.s {
  margin-left: auto;
  font-size: 0.72rem;
  color: var(--mute);
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.s::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentcolor;
  opacity: 0.5;
}

.gen .s {
  color: var(--accent);
}

.gen .s::before {
  opacity: 1;
  animation: pulse 1s ease-in-out infinite;
}

.ready .s {
  color: var(--ok);
}

.ready .s::before {
  opacity: 1;
}

.edited .s {
  color: var(--ink);
}
</style>
