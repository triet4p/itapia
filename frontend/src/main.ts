/**
 * main.ts
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Plugin imports
import { registerPlugins } from '@/plugins';

// Component imports
import App from './App.vue';

// Vue composable imports
import { createApp } from 'vue';

// Global style imports
import 'unfonts.css';

// Store imports
import { useAuthStore } from './stores/authStore';
import { createPinia } from 'pinia';

// Router import
import router from './router';

// Vuetify import
import vuetify from './plugins/vuetify';

// Create the main Vue application instance
const app = createApp(App);

// Register core plugins
app.use(createPinia());
app.use(router);
app.use(vuetify);

// Register additional plugins
registerPlugins(app);

// 2. Initialize and call action after Pinia has been used
const authStore = useAuthStore();
authStore.initializeAuth();

// Mount the application to the DOM
app.mount('#app');
