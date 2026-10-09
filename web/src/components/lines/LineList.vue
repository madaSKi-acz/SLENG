<!--
  Purpose: The script as lines: click a number to play from there, click text to correct it.
  Layer:   web/components/lines
  Depends: stores/{script, playback}, LineRow
-->
<script setup lang="ts">
import LineRow from '@/components/lines/LineRow.vue';
import { useText } from '@/composables/useText';
import { usePlaybackStore } from '@/stores/playback';
import { useScriptStore } from '@/stores/script';

const script = useScriptStore();
const playback = usePlaybackStore();
const { t } = useText();
</script>

<template>
  <section class="panel" :aria-label="t('lines')">
    <h2>
      <span>{{ t('lines') }}</span><small>{{ t('lines_hint') }}</small>
    </h2>
    <p v-if="!script.lines.length" class="empty">
      <b>{{ t('empty_title') }}</b><span>{{ t('empty_body') }}</span>
    </p>
    <ol v-else>
      <LineRow
        v-for="(line, index) in script.lines"
        :key="`${script.splitId}-${index}`"
        :index="index"
        :line="line"
        :playing="playback.current === index"
        @play="playback.speak"
        @edit="script.editLine"
      />
    </ol>
  </section>
</template>

<style scoped>
ol {
  list-style: none;
  margin: 0 -6px;
  padding: 0;
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: var(--mute);
  font-size: 0.8125rem;
  margin: 0;
  padding: 24px 8px;
  text-align: center;
  border: 1px dashed var(--line-strong);
  border-radius: var(--r-md);
}

.empty b {
  color: var(--ink);
}
</style>
