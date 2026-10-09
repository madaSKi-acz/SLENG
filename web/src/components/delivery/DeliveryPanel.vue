<!--
  Purpose: How the script is read: voice cleanup, speed, pauses, line length, smart merge.
  Layer:   web/components/delivery
  Depends: stores/{settings, options}, ui/{SegmentedControl, SliderField, SwitchField}
-->
<script setup lang="ts">
import { computed } from 'vue';

import type { CleanupLevel } from '@/api/types';
import SegmentedControl from '@/components/ui/SegmentedControl.vue';
import SliderField from '@/components/ui/SliderField.vue';
import SwitchField from '@/components/ui/SwitchField.vue';
import { useText } from '@/composables/useText';
import { useOptionsStore } from '@/stores/options';
import { useSettingsStore } from '@/stores/settings';

const settings = useSettingsStore();
const options = useOptionsStore();
const { t } = useText();

const levels = computed(() =>
  options.cleanup_levels.map((level: CleanupLevel) => ({
    value: level,
    label: t(`fx_${level}_l`),
  })),
);
const seconds = (value: number): string => t('unit_sec', { n: value });
</script>

<template>
  <section class="sec" :aria-label="t('delivery')">
    <h2>{{ t('delivery') }}</h2>
    <div class="field">
      <span class="top">{{ t('cleanup') }}</span>
      <SegmentedControl v-model="settings.cleanup" :options="levels" :label="t('cleanup')" />
      <p class="hint note">{{ t(`fx_${settings.cleanup}`) }}</p>
    </div>
    <SliderField
      v-model="settings.speed"
      :label="t('speed')"
      :display="t('unit_times', { n: settings.speed })"
      :min="0.6"
      :max="1.4"
      :step="0.05"
    />
    <SliderField
      v-model="settings.sentencePause"
      :label="t('pause_s')"
      :display="seconds(settings.sentencePause)"
      :min="0"
      :max="1.5"
      :step="0.05"
    />
    <SliderField
      v-model="settings.paragraphPause"
      :label="t('pause_p')"
      :display="seconds(settings.paragraphPause)"
      :min="0"
      :max="2.5"
      :step="0.1"
    />
    <details>
      <summary>{{ t('more') }}</summary>
      <SliderField
        v-model="settings.maxChars"
        :label="t('maxlen')"
        :display="t('unit_chars', { n: settings.maxChars })"
        :min="40"
        :max="400"
        :step="10"
      />
      <SwitchField v-model="settings.smart" class="smart" :label="t('smart')" />
    </details>
  </section>
</template>

<style scoped>
.note {
  margin-top: 6px;
}

.smart {
  margin-top: 10px;
}
</style>
