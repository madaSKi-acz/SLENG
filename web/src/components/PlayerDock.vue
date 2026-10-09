<!--
  Purpose: Bottom bar: pause/resume, the line being spoken, status, progress, line counter.
  Layer:   web/components
  Depends: stores/{playback, script, status}, ui/Icon
-->
<script setup lang="ts">
import { computed } from 'vue';

import Icon from '@/components/ui/Icon.vue';
import { useText } from '@/composables/useText';
import { usePlaybackStore } from '@/stores/playback';
import { useScriptStore } from '@/stores/script';
import { useStatusStore } from '@/stores/status';

const playback = usePlaybackStore();
const script = useScriptStore();
const status = useStatusStore();
const { t, render } = useText();

const nowText = computed(() => script.lines[playback.current]?.text ?? '');
const counter = computed(() =>
  playback.current >= 0 ? `${playback.current + 1} / ${script.lines.length}` : '',
);
</script>

<template>
  <div class="dock">
    <button
      class="pp"
      :disabled="!playback.busy"
      :aria-label="t(playback.playing ? 'pause' : 'resume')"
      @click="playback.toggle()"
    >
      <Icon :name="playback.playing ? 'pause' : 'play'" />
    </button>
    <div class="now">
      <div v-if="nowText" class="line">{{ nowText }}</div>
      <div class="status" :class="{ 'err-text': status.error }" aria-live="polite">
        {{ render(status.message) }}
      </div>
      <div class="bar"><i :style="{ width: `${status.progress * 100}%` }" /></div>
    </div>
    <span class="counter">{{ counter }}</span>
    <span class="keys">{{ t('shortcuts') }}</span>
  </div>
</template>

<style scoped>
.dock {
  position: sticky;
  bottom: 0;
  z-index: 20;
  min-height: var(--dock-h);
  padding: 10px clamp(16px, 3vw, 32px);
  background: var(--surface);
  border-top: 1px solid var(--line);
  display: flex;
  gap: 14px;
  align-items: center;
}

.pp {
  flex: none;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  padding: 0;
  background: var(--accent);
  color: var(--accent-ink);
  border: 0;
}

.pp:hover:not(:disabled) {
  background: var(--accent) !important;
  filter: brightness(1.07);
}

.pp .ic {
  width: 14px;
  height: 14px;
}

.now {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.line {
  font-size: 0.875rem;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status {
  font-size: 0.78rem;
  color: var(--mute);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status.err-text {
  color: var(--err);
}

.bar {
  height: 3px;
  background: var(--line);
  border-radius: 2px;
  overflow: hidden;
  margin-top: 4px;
}

.bar i {
  display: block;
  height: 100%;
  background: var(--accent);
  transition: width 0.25s;
}

.counter,
.keys {
  font-size: 0.78rem;
  color: var(--mute);
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

@media (width <= 700px) {
  .keys {
    display: none;
  }
}
</style>
