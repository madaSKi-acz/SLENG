<!--
  Purpose: Labelled on/off switch (a styled checkbox).
  Layer:   web/components/ui
  Props:   v-model (boolean), label
-->
<script setup lang="ts">
const model = defineModel<boolean>({ required: true });
defineProps<{ label: string }>();
</script>

<template>
  <label class="switch">
    <span>{{ label }}</span>
    <input v-model="model" type="checkbox" />
  </label>
</template>

<style scoped>
.switch {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 0.8125rem;
  cursor: pointer;
  padding: 4px 0;
}

.switch input {
  appearance: none;
  flex: none;
  width: 30px;
  height: 18px;
  margin: 0;
  border-radius: 999px;
  background: var(--line-strong);
  position: relative;
  cursor: pointer;
  transition: background 0.15s;
}

.switch input::before {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.15s;
  box-shadow: 0 1px 2px rgb(0 0 0 / 20%);
}

.switch input:checked {
  background: var(--accent);
}

.switch input:checked::before {
  transform: translateX(12px);
}
</style>
