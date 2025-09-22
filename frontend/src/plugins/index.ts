/**
 * plugins/index.ts
 *
 * Automatically included in `./src/main.ts`
 */

// Plugin imports
import vuetify from './vuetify';
import pinia from '../stores';
import router from '../router';

// Vue type imports
import type { App } from 'vue';

/**
 * Registers all plugins with the Vue application.
 * 
 * @param app - The Vue application instance
 */
export function registerPlugins (app: App) {
  app
    .use(vuetify)
    .use(router)
    .use(pinia);
}
