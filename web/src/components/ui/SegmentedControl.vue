<!--
  Purpose: Mutually exclusive options as a segmented control (an accessible radio group).
  Layer:   web/components/ui
  Props:   v-model, options (Choice[]), label (aria), compact? · Emits: update:modelValue
-->
<script setup lang="ts" generic="V extends string">
import { useId } from 'vue';

import Icon from '@/components/ui/Icon.vue';
import type { Choice } from '@/components/ui/types';

const model = defineModel<V>({ required: true });
defineProps<{ options: Choice<V>[]; label: string; compact?: boolean }>();
const group = useId();
</script>

<template>
  <div class="seg" :class="{ compact }" role="radiogroup" :aria-label="label">
    <label v-for="option in options" :key="option.value">
      <input
        type="radio"
        :name="group"
        :value="option.value"
        :checked="option.value === model"
        @change="model = option.value"
      />
      <Icon v-if="option.icon" :name="option.icon" />
      <span>{{ option.label }}</span>
    </label>
  </div>
</template>

<style scoped>
.seg {
  display: flex;
  padding: 2px;
  gap: 2px;
  background: var(--sunk);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
}

.seg label {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  text-align: center;
  padding: 5px 10px;
  border-radius: var(--r-sm);
  cursor: pointer;
  color: var(--mute);
  font-size: 0.8125rem;
  white-space: nowrap;
}

.seg label:hover {
  color: var(--ink);
}

.seg input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.seg label:has(input:checked) {
  background: var(--surface);
  color: var(--ink);
  font-weight: 700;
  box-shadow: 0 0 0 1px var(--line-strong);
}

.seg label:has(input:focus-visible) {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}

.compact {
  flex: none;
}

.compact label {
  padding: 4px 10px;
}
</style>
