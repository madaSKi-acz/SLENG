<!--
  Purpose: Find & replace across the whole script (plain text, every occurrence).
  Layer:   web/components/editor
  Depends: stores/script, composables/useText
-->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

import { useText } from '@/composables/useText';
import { useScriptStore } from '@/stores/script';
import type { Message } from '@/stores/status';

const script = useScriptStore();
const { t, render } = useText();
const needle = ref('');
const replacement = ref('');
const result = ref<Message | null>(null);
const input = ref<HTMLInputElement | null>(null);

const occurrences = (text: string, part: string): number => text.split(part).length - 1;

const info = computed(() => {
  if (result.value) return render(result.value);
  return needle.value ? t('m_found', { n: occurrences(script.text, needle.value) }) : '';
});

function replaceAll(): void {
  if (!needle.value) return;
  const count = occurrences(script.text, needle.value);
  script.setText(script.text.split(needle.value).join(replacement.value));
  result.value = { key: 'm_replaced', vars: { n: count } };
}

onMounted(() => input.value?.focus());
</script>

<template>
  <div class="find">
    <input
      ref="input"
      v-model="needle"
      type="text"
      :placeholder="t('find_ph')"
      :aria-label="t('find_ph')"
      @input="result = null"
    />
    <input
      v-model="replacement"
      type="text"
      :placeholder="t('replace_ph')"
      :aria-label="t('replace_ph')"
    />
    <button @click="replaceAll">{{ t('replace_all') }}</button>
    <span class="hint">{{ info }}</span>
  </div>
</template>

<style scoped>
.find {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  margin-bottom: 10px;
}

.find input {
  flex: 1;
  min-width: 120px;
}
</style>
