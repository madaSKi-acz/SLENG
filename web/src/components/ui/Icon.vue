<!--
  Purpose: One icon from the sprite (IconSprite.vue).
  Layer:   web/components/ui
  Props:   name (symbol id without the "i-" prefix)
-->
<script setup lang="ts">
defineProps<{ name: string }>();
</script>

<template>
  <svg class="ic" aria-hidden="true"><use :href="`#i-${name}`" /></svg>
</template>
