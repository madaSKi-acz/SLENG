/**
 * Purpose: Global keys: Ctrl/⌘+Enter speaks, Esc stops (unless a dialog or full screen owns it).
 * Layer:   web/composables
 * Exports: useShortcuts
 * Depends: vue, stores/{playback, ui}
 */
import { onBeforeUnmount, onMounted } from 'vue';

import { usePlaybackStore } from '@/stores/playback';
import { useUiStore } from '@/stores/ui';

export function useShortcuts(): void {
  const playback = usePlaybackStore();
  const ui = useUiStore();
  const onKey = (event: KeyboardEvent): void => {
    const speakKey = event.key === 'Enter' && (event.ctrlKey || event.metaKey);
    if (speakKey && !playback.busy) {
      event.preventDefault();
      void playback.speak();
    } else if (event.key === 'Escape' && playback.busy && !ui.cloneOpen && !ui.editorFull) {
      playback.stop();
    }
  };
  onMounted(() => document.addEventListener('keydown', onKey));
  onBeforeUnmount(() => document.removeEventListener('keydown', onKey));
}
