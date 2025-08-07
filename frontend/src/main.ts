/**
 * main.ts
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Plugins
import { registerPlugins } from '@/plugins'

// Components
import App from './App.vue'

// Composables
import { createApp } from 'vue'

// Styles
import 'unfonts.css'

import { useAuthStore } from './stores/authStore'
import { createPinia } from 'pinia'
import router from './router'
import vuetify from './plugins/vuetify'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(vuetify)

registerPlugins(app)

// 2. Khởi tạo và gọi action sau khi Pinia đã được use()
const authStore = useAuthStore()
authStore.initializeAuth()

app.mount('#app')
