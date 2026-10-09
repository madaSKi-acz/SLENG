<!--
  Purpose: Video export: title, size, look, colours, design number, caption switches, MP4/SRT.
  Layer:   web/components/export
  Depends: stores/{settings, options, exports}, SizeTiles, ui/{Icon, SwitchField}
-->
<script setup lang="ts">
import { computed } from 'vue';

import SizeTiles from '@/components/export/SizeTiles.vue';
import Icon from '@/components/ui/Icon.vue';
import SwitchField from '@/components/ui/SwitchField.vue';
import { useText } from '@/composables/useText';
import { useExportsStore } from '@/stores/exports';
import { useOptionsStore } from '@/stores/options';
import { useSettingsStore } from '@/stores/settings';

const settings = useSettingsStore();
const video = computed(() => settings.video);
const options = useOptionsStore();
const exports = useExportsStore();
const { t } = useText();

const paletteGroups = computed(() =>
  (['pop', 'other'] as const).map((group) => ({
    group,
    names: options.palettes.filter((p) => p.group === group).map((p) => p.name),
  })),
);
</script>

<template>
  <div class="stack">
    <input
      v-model="video.title"
      type="text"
      :placeholder="t('title_ph')"
      :aria-label="t('title_ph')"
    />
    <p class="label">{{ t('size') }}</p>
    <SizeTiles v-model="video.size" :sizes="options.sizes" />
    <p class="label">{{ t('look') }}</p>
    <select v-model="video.theme" :aria-label="t('look')">
      <option v-for="theme in options.themes" :key="theme" :value="theme">
        {{ t(`th_${theme}`) }}
      </option>
    </select>
    <div class="pair">
      <select v-model="video.palette" :aria-label="t('colours')">
        <optgroup v-for="entry in paletteGroups" :key="entry.group" :label="t(`pg_${entry.group}`)">
          <option v-for="name in entry.names" :key="name" :value="name">
            {{ t(`vp_${name}`) }}
          </option>
        </optgroup>
      </select>
      <input
        v-model="video.seed"
        type="text"
        inputmode="numeric"
        :placeholder="t('seed_ph')"
        :aria-label="t('seed_ph')"
        :title="t('seed_title')"
      />
    </div>
    <div class="switches">
      <SwitchField v-model="video.subtitles" :label="t('burn')" />
      <SwitchField v-model="video.karaoke" :label="t('karaoke')" />
      <SwitchField v-model="video.progressBar" :label="t('progress')" />
      <SwitchField v-model="video.titleCard" :label="t('intro')" />
    </div>
    <button
      class="primary"
      :class="{ loading: exports.busy === 'mp4' }"
      :disabled="!!exports.busy"
      @click="exports.video()"
    >
      <Icon name="video" /><span>{{ t('mp4') }}</span>
    </button>
    <button
      :class="{ loading: exports.busy === 'srt' }"
      :disabled="!!exports.busy"
      @click="exports.download('srt')"
    >
      <Icon name="cc" /><span>{{ t('srt') }}</span>
    </button>
  </div>
</template>

<style scoped>
.pair {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.switches {
  display: flex;
  flex-direction: column;
  padding: 4px 0;
}
</style>
