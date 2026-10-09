<!--
  Purpose: A voice's stable bar pattern; the bars "talk" while that voice is speaking.
  Layer:   web/components/ui
  Props:   id (any string), talking?
-->
<script setup lang="ts">
import { computed } from 'vue';

import { voiceprint } from '@/lib/voiceprint';

const props = defineProps<{ id: string; talking?: boolean }>();
const bars = computed(() => voiceprint(props.id));
</script>

<template>
  <span class="vp" :class="{ talking }" aria-hidden="true">
    <i v-for="(height, k) in bars" :key="k" :style="{ '--h': height.toFixed(2), '--k': k }" />
  </span>
</template>

<style scoped>
.vp {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 18px;
}

.vp i {
  display: block;
  width: 2.5px;
  height: calc(var(--h) * 100%);
  border-radius: 2px;
  background: currentcolor;
  transform-origin: bottom;
}

.talking i {
  animation: talk 0.9s ease-in-out infinite alternate;
  animation-delay: calc(var(--k) * -73ms);
}

@keyframes talk {
  to {
    transform: scaleY(0.25);
  }
}
</style>
