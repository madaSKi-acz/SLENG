<!--
  Purpose: Labelled range slider with its current value shown on the right.
  Layer:   web/components/ui
  Props:   v-model (number), label, display (formatted value), min, max, step
-->
<script setup lang="ts">
const model = defineModel<number>({ required: true });
defineProps<{ label: string; display: string; min: number; max: number; step: number }>();
</script>

<template>
  <label class="field">
    <span class="top">
      <span>{{ label }}</span>
      <b>{{ display }}</b>
    </span>
    <input v-model.number="model" type="range" :min="min" :max="max" :step="step" />
  </label>
</template>
