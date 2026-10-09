/**
 * Purpose: Vite config: Vue plugin, "@" alias, engine fonts, and the /api proxy to the engine.
 * Layer:   web tooling
 * Notes:   The fonts live once, in the engine package; "@fonts" points there (fs.allow lets the
 *          dev server read outside web/). Set SLENG_ENGINE_URL to proxy to another engine.
 */
import { URL, fileURLToPath } from 'node:url';

import vue from '@vitejs/plugin-vue';
import { defineConfig } from 'vite';

const engineUrl = process.env.SLENG_ENGINE_URL ?? 'http://127.0.0.1:7860';
const local = (path: string): string => fileURLToPath(new URL(path, import.meta.url));

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': local('./src'),
      '@fonts': local('../engine/src/sleng/assets/fonts'),
    },
  },
  server: {
    port: 5173,
    proxy: { '/api': engineUrl },
    fs: { allow: ['..'] },
  },
  build: { outDir: 'dist', sourcemap: true },
});
