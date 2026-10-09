<!--
  Purpose: Top bar: brand voiceprint, title, language switch, appearance menu.
  Layer:   web/components
  Depends: stores/appearance, ui/{SegmentedControl, VoicePrint}, AppearanceMenu
-->
<script setup lang="ts">
import { computed } from 'vue';

import AppearanceMenu from '@/components/AppearanceMenu.vue';
import SegmentedControl from '@/components/ui/SegmentedControl.vue';
import VoicePrint from '@/components/ui/VoicePrint.vue';
import { useText } from '@/composables/useText';
import type { Locale } from '@/i18n';
import { useAppearanceStore } from '@/stores/appearance';

const appearance = useAppearanceStore();
const { t } = useText();
const languages = [
  { value: 'en' as Locale, label: 'EN' },
  { value: 'km' as Locale, label: 'ខ្មែរ' },
];
const locale = computed({
  get: () => appearance.locale,
  set: (value: Locale) => appearance.setLocale(value),
});
</script>

<template>
  <header class="appbar">
    <VoicePrint id="អត្ថបទទៅជាសំឡេង" class="brand" />
    <div class="titles">
      <h1>{{ t('app_title') }}</h1>
      <p>{{ t('tagline') }}</p>
    </div>
    <SegmentedControl v-model="locale" :options="languages" :label="t('language')" compact />
    <AppearanceMenu />
  </header>
</template>

<style scoped>
.appbar {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 56px;
  padding: 8px clamp(16px, 3vw, 32px);
  background: var(--surface);
  border-bottom: 1px solid var(--line);
}

.brand {
  height: 22px;
  color: var(--accent);
}

.titles {
  min-width: 0;
  flex: 1;
}

h1 {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  line-height: 1.3;
}

p {
  margin: 0;
  color: var(--mute);
  font-size: 0.8rem;
  line-height: 1.35;
}

@media (width <= 640px) {
  p {
    display: none;
  }
}
</style>
