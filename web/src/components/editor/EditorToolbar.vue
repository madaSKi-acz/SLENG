<!--
  Purpose: Editor tool row: open .txt, paste, clear, find & replace, text size, full screen.
  Layer:   web/components/editor
  Props:   full · Emits: open(File), paste, clear, find, scale(step), full
-->
<script setup lang="ts">
import Icon from '@/components/ui/Icon.vue';
import { useText } from '@/composables/useText';

defineProps<{ full: boolean }>();
const emit = defineEmits<{
  open: [file: File];
  paste: [];
  clear: [];
  find: [];
  scale: [step: number];
  full: [];
}>();
const { t } = useText();
const SCALE_STEP = 0.1;

function onFile(event: Event): void {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (file) emit('open', file);
  input.value = '';
}
</script>

<template>
  <div class="tools">
    <label class="btn quiet">
      <Icon name="file" /><span>{{ t('open_txt') }}</span>
      <input type="file" accept=".txt,text/plain" hidden @change="onFile" />
    </label>
    <button class="quiet" @click="emit('paste')">
      <Icon name="paste" /><span>{{ t('paste') }}</span>
    </button>
    <button class="quiet" @click="emit('clear')">
      <Icon name="trash" /><span>{{ t('clear') }}</span>
    </button>
    <span class="sep" />
    <button class="quiet" @click="emit('find')">
      <Icon name="search" /><span>{{ t('find') }}</span>
    </button>
    <span class="grow" />
    <button
      class="quiet"
      :title="t('smaller')"
      :aria-label="t('smaller')"
      @click="emit('scale', -SCALE_STEP)"
    >
      A−
    </button>
    <button
      class="quiet"
      :title="t('larger')"
      :aria-label="t('larger')"
      @click="emit('scale', SCALE_STEP)"
    >
      A+
    </button>
    <span class="sep" />
    <button class="quiet" @click="emit('full')">
      <Icon :name="full ? 'x' : 'expand'" /><span>{{ t(full ? 'exit_full' : 'full') }}</span>
    </button>
  </div>
</template>

<style scoped>
.tools {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  align-items: center;
  margin: -6px -6px 10px;
}
</style>
