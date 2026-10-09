<!--
  Purpose: Export section: Audio tab (WAV, per-line zip) and Video tab (VideoExport).
  Layer:   web/components/export
  Depends: stores/{settings, exports}, VideoExport, ui/{Icon, SegmentedControl}
-->
<script setup lang="ts">
import { computed } from 'vue';

import VideoExport from '@/components/export/VideoExport.vue';
import Icon from '@/components/ui/Icon.vue';
import SegmentedControl from '@/components/ui/SegmentedControl.vue';
import { useText } from '@/composables/useText';
import { useExportsStore } from '@/stores/exports';
import { useSettingsStore } from '@/stores/settings';

const settings = useSettingsStore();
const exports = useExportsStore();
const { t } = useText();
const tabs = computed(() => [
  { value: 'audio' as const, label: t('tab_audio') },
  { value: 'video' as const, label: t('tab_video') },
]);
</script>

<template>
  <section class="sec" :aria-label="t('export')">
    <h2>{{ t('export') }}</h2>
    <SegmentedControl
      v-model="settings.exportTab"
      class="tabs"
      :options="tabs"
      :label="t('export')"
    />
    <div v-if="settings.exportTab === 'audio'" class="stack">
      <button
        class="primary"
        :class="{ loading: exports.busy === 'wav' }"
        :disabled="!!exports.busy"
        @click="exports.download('wav')"
      >
        <Icon name="download" /><span>{{ t('dl_wav') }}</span>
      </button>
      <button
        :class="{ loading: exports.busy === 'zip' }"
        :disabled="!!exports.busy"
        @click="exports.download('zip')"
      >
        <Icon name="archive" /><span>{{ t('zip') }}</span>
      </button>
      <p class="hint">{{ t('uses_edited') }}</p>
    </div>
    <VideoExport v-else />
  </section>
</template>

<style scoped>
.tabs {
  margin-bottom: 14px;
}
</style>
