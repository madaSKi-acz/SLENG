<!--
  Purpose: Video frame sizes as tiles showing each aspect ratio.
  Layer:   web/components/export
  Props:   v-model ("WIDTHxHEIGHT"), sizes (from the engine)
-->
<script setup lang="ts">
import type { FrameSize } from '@/api/types';
import { useText } from '@/composables/useText';

const model = defineModel<string>({ required: true });
defineProps<{ sizes: FrameSize[] }>();
const { t } = useText();
const key = (size: FrameSize): string => `${size.width}x${size.height}`;
</script>

<template>
  <div class="sizes" role="radiogroup" :aria-label="t('size')">
    <button
      v-for="size in sizes"
      :key="key(size)"
      type="button"
      class="size"
      role="radio"
      :aria-checked="model === key(size)"
      :title="`${size.width}×${size.height}`"
      @click="model = key(size)"
    >
      <span class="ratio" :style="{ aspectRatio: `${size.width} / ${size.height}` }" />
      <span>{{ t(`sz_${key(size)}`) }}</span>
    </button>
  </div>
</template>

<style scoped>
.sizes {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
}

.size {
  flex-direction: column;
  justify-content: flex-end;
  gap: 6px;
  padding: 9px 4px 6px;
  font-size: 0.7rem;
  color: var(--mute);
  border-color: var(--line);
}

.ratio {
  display: block;
  height: 20px;
  border: 1.5px solid currentcolor;
  border-radius: 3px;
}

.size[aria-checked='true'] {
  color: var(--accent);
  border-color: var(--accent);
  background: var(--accent-soft);
  font-weight: 700;
}
</style>
