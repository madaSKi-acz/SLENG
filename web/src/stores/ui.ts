/**
 * Purpose: Interface state shared by components: full-screen editor, clone dialog.
 * Layer:   web/stores
 * Exports: useUiStore
 * Depends: pinia
 */
import { defineStore } from 'pinia';

export const useUiStore = defineStore('ui', {
  state: () => ({ editorFull: false, cloneOpen: false }),
});
