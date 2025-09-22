/**
 * plugins/vuetify.ts
 *
 * Vuetify plugin configuration
 * 
 * Framework documentation: https://vuetifyjs.com`
 */

// Vuetify styles
import '@mdi/font/css/materialdesignicons.css';
import 'vuetify/styles';

// Vuetify composables
import { createVuetify } from 'vuetify';

/**
 * Creates and configures the Vuetify instance.
 * 
 * https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
 */
export default createVuetify({
  theme: {
    defaultTheme: 'system',
  },
});
