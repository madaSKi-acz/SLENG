<!--
  Purpose: Appearance popover: light/dark/system mode and the accent colour.
  Layer:   web/components
  Depends: stores/appearance, ui/{Icon, SegmentedControl}
  Notes:   Closes on outside click and on Esc (focus returns to the button).
-->
<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';

import Icon from '@/components/ui/Icon.vue';
import SegmentedControl from '@/components/ui/SegmentedControl.vue';
import { useText } from '@/composables/useText';
import { ACCENTS, type Accent, type Mode, useAppearanceStore } from '@/stores/appearance';

const SWATCHES: Record<Accent, string> = {
  indigo: '#4150c9',
  teal: '#0f766e',
  graphite: '#2b313b',
  plum: '#7b3fa6',
};
const ICONS: Record<Mode, string> = { system: 'monitor', light: 'sun', dark: 'moon' };

const appearance = useAppearanceStore();
const { t } = useText();
const open = ref(false);
const root = ref<HTMLElement | null>(null);
const button = ref<HTMLButtonElement | null>(null);

const modes = computed(() =>
  (Object.keys(ICONS) as Mode[]).map((mode) => ({
    value: mode,
    label: t(`mode_${mode}`),
    icon: ICONS[mode],
  })),
);
const mode = computed({
  get: () => appearance.mode,
  set: (value: Mode) => appearance.setMode(value),
});

function onDocumentClick(event: MouseEvent): void {
  if (open.value && !root.value?.contains(event.target as Node)) open.value = false;
}

function onKey(event: KeyboardEvent): void {
  if (event.key !== 'Escape' || !open.value) return;
  open.value = false;
  button.value?.focus();
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick);
  document.addEventListener('keydown', onKey);
});
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick);
  document.removeEventListener('keydown', onKey);
});
</script>

<template>
  <div ref="root" class="menuwrap">
    <button
      ref="button"
      class="iconbtn"
      aria-haspopup="true"
      :aria-expanded="open"
      :title="t('appearance')"
      :aria-label="t('appearance')"
      @click="open = !open"
    >
      <Icon name="contrast" />
    </button>
    <div v-if="open" class="menu">
      <p class="label">{{ t('mode') }}</p>
      <SegmentedControl v-model="mode" :options="modes" :label="t('mode')" />
      <p class="label">{{ t('accent_colour') }}</p>
      <div class="swatches" role="radiogroup" :aria-label="t('accent_colour')">
        <label v-for="accent in ACCENTS" :key="accent">
          <input
            type="radio"
            name="accent"
            :checked="appearance.accent === accent"
            @change="appearance.setAccent(accent)"
          />
          <span class="dot" :style="{ '--c': SWATCHES[accent] }" />
          <span>{{ t(`accent_${accent}`) }}</span>
        </label>
      </div>
    </div>
  </div>
</template>

<style scoped>
.menuwrap {
  position: relative;
}

.iconbtn {
  width: 34px;
  height: 34px;
  padding: 0;
  border-color: var(--line);
}

.menu {
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  z-index: 40;
  width: 260px;
  padding: 14px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  box-shadow: 0 12px 32px rgb(16 24 40 / 16%);
}

.menu .label {
  margin: 0 0 6px;
}

.menu .label + * {
  margin-bottom: 14px;
}

.swatches {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
}

.swatches label {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: var(--r-sm);
  cursor: pointer;
  font-size: 0.8125rem;
  border: 1px solid transparent;
}

.swatches label:hover {
  background: var(--sunk);
}

.swatches input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.swatches label:has(input:checked) {
  border-color: var(--line-strong);
  font-weight: 700;
}

.swatches label:has(input:focus-visible) {
  outline: 2px solid var(--accent);
}

.dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--c);
}
</style>
