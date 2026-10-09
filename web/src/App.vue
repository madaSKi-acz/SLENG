<!--
  Purpose: Page layout: app bar, script + lines, settings rail, clone dialog, player dock, toasts.
  Layer:   web/root
  Depends: every top-level component; stores/{voices, options}; composables/useShortcuts
-->
<script setup lang="ts">
import { onMounted } from 'vue';

import AppBar from '@/components/AppBar.vue';
import PlayerDock from '@/components/PlayerDock.vue';
import DeliveryPanel from '@/components/delivery/DeliveryPanel.vue';
import ScriptEditor from '@/components/editor/ScriptEditor.vue';
import ExportPanel from '@/components/export/ExportPanel.vue';
import LineList from '@/components/lines/LineList.vue';
import IconSprite from '@/components/ui/IconSprite.vue';
import ToastStack from '@/components/ui/ToastStack.vue';
import CloneDialog from '@/components/voices/CloneDialog.vue';
import VoicePanel from '@/components/voices/VoicePanel.vue';
import { useShortcuts } from '@/composables/useShortcuts';
import { useOptionsStore } from '@/stores/options';
import { useVoicesStore } from '@/stores/voices';

const voices = useVoicesStore();
const options = useOptionsStore();
useShortcuts();
onMounted(() => {
  void voices.load();
  void options.load();
});
</script>

<template>
  <IconSprite />
  <AppBar />
  <main class="studio">
    <div class="main">
      <ScriptEditor />
      <LineList />
    </div>
    <aside class="rail panel">
      <VoicePanel />
      <DeliveryPanel />
      <ExportPanel />
    </aside>
  </main>
  <CloneDialog />
  <PlayerDock />
  <ToastStack />
</template>
