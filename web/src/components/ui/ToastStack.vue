<!--
  Purpose: Short-lived notifications in the bottom-right corner.
  Layer:   web/components/ui
  Depends: stores/status, composables/useText
-->
<script setup lang="ts">
import { useText } from '@/composables/useText';
import { useStatusStore } from '@/stores/status';

const status = useStatusStore();
const { render } = useText();
</script>

<template>
  <div class="toasts" aria-live="polite">
    <div v-for="toast in status.toasts" :key="toast.id" class="toast" :class="{ err: toast.error }">
      {{ render(toast.message) }}
    </div>
  </div>
</template>

<style scoped>
.toasts {
  position: fixed;
  right: 20px;
  bottom: calc(var(--dock-h) + 16px);
  z-index: 60;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}

.toast {
  background: var(--ink);
  color: var(--surface);
  padding: 9px 14px;
  border-radius: var(--r-md);
  font-size: 0.8125rem;
  box-shadow: 0 8px 24px rgb(0 0 0 / 18%);
  animation: rise 0.2s ease;
  max-width: 380px;
}

.toast.err {
  background: var(--err);
  color: #fff;
}

@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
}
</style>
