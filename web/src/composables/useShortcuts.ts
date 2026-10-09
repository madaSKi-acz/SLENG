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
  const isSpeakKey = (event: KeyboardEvent): boolean =>
    event.key === 'Enter' && (event.ctrlKey || event.metaKey);
  const mayStop = (): boolean => playback.busy && !ui.cloneOpen && !ui.editorFull;
  const onKey = (event: KeyboardEvent): void => {
    if (isSpeakKey(event) && !playback.busy) {
      event.preventDefault();
      void playback.speak();
    } else if (event.key === 'Escape' && mayStop()) {
      playback.stop();
    }
  };
  onMounted(() => document.addEventListener('keydown', onKey));
  onBeforeUnmount(() => document.removeEventListener('keydown', onKey));
}
