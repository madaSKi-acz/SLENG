/**
 * Purpose: Ambient types: Vite env variables and .vue modules.
 * Layer:   web/types
 */
/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Engine API base, e.g. http://127.0.0.1:7860/api/v1 (desktop build). Default: /api/v1 */
  readonly VITE_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue';
  const component: DefineComponent<object, object, unknown>;
  export default component;
}
