<script lang="ts" setup>
import { RouterView } from 'vue-router';
import { VApp } from 'vuetify/components';

import { useAuthStore } from '@/stores/authStore';

const authStore = useAuthStore();
const { isLoggedIn, user } = storeToRefs(authStore);

function handleLogout() {
  authStore.logout();
}
</script>

<template>
  <v-app>
    <v-app-bar app color="primary" dark elevation="2">
      <VAppBarTitle>
        <VBtn to="/" variant="text" class="text-h6">ITAPIA</VBtn>
      </VAppBarTitle>

      <VSpacer></VSpacer>

      <VBtn to="/analysis" prepend-icon="mdi-magnify">Advanced Analysis</VBtn>
      <VBtn to="/advisor" prepend-icon="mdi-lightbulb-on-outline">Advisor</VBtn>
      <VBtn to="/rules" prepend-icon="mdi-book-open-variant">Rules Library</VBtn>

      <VDivider vertical class="mx-2"></VDivider>

      <!-- 3. HIỂN THỊ CÓ ĐIỀU KIỆN -->
      <div v-if="isLoggedIn">
        <!-- Hiển thị khi đã đăng nhập -->
        <v-chip color="white" text-color="primary" class="mr-2">
          <v-icon start>mdi-account-circle-outline</v-icon>
          {{ user?.full_name }}
        </v-chip>
        <v-btn icon="mdi-logout" @click="handleLogout"></v-btn>
      </div>
      <div v-else>
        <!-- Hiển thị khi chưa đăng nhập -->
        <v-btn to="/login" variant="outlined">
          <v-icon start>mdi-login</v-icon>
          Login
        </v-btn>
      </div>
    </v-app-bar>
    <v-main>
      <RouterView />
    </v-main>
    <v-footer app>
      <span>&copy; {{ new Date().getFullYear() }} - ITAPIA Project</span>
    </v-footer>
  </v-app>
</template>

<style scoped>
/* Thêm một chút style để tiêu đề trông đẹp hơn */
.v-app-bar-title .v-btn {
  text-transform: none; /* Bỏ viết hoa mặc định của nút */
  font-weight: bold;
}
</style>