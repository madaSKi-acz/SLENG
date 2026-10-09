/**
 * Purpose: Start the app: styles, Pinia, i18n, saved settings, theme; mount <App>.
 * Layer:   web/root
 * Depends: vue, pinia, i18n, stores/{settings, appearance}, App.vue
 */
import { createPinia } from 'pinia';
import { createApp } from 'vue';

import App from '@/App.vue';
import { i18n } from '@/i18n';
import { useAppearanceStore } from '@/stores/appearance';
import { useSettingsStore } from '@/stores/settings';
import '@/styles/fonts.css';
import '@/styles/tokens.css';
import '@/styles/base.css';
import '@/styles/controls.css';
import '@/styles/layout.css';

const pinia = createPinia();
const app = createApp(App).use(pinia).use(i18n);

const settings = useSettingsStore(pinia);
settings.$subscribe(() => settings.persist());

const appearance = useAppearanceStore(pinia);
appearance.apply();
appearance.followSystem();

app.mount('#app');
