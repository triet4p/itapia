<script lang="ts" setup>
import { RouterView } from 'vue-router';
import { VApp } from 'vuetify/components';

import { useAuthStore } from '@/stores/authStore';
import { useNotificationStore } from '@/stores/notificationStore';

const authStore = useAuthStore();
const { isLoggedIn, user } = storeToRefs(authStore);

const notificationStore = useNotificationStore();
const { message, color, visible, timeout } = storeToRefs(notificationStore);

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
      <!-- BẮT ĐẦU THAY ĐỔI: USER MENU -->
      <div v-if="authStore.isLoggedIn">
        <v-menu>
          <!-- 1. PHẦN KÍCH HOẠT (ACTIVATOR) -->
          <template v-slot:activator="{ props }">
            <v-chip v-bind="props" color="white" text-color="primary" class="mr-2" style="cursor: pointer;">
              <v-avatar start>
                <v-img v-if="authStore.user?.avatar_url && authStore.user?.full_name" 
                :src="authStore.user?.avatar_url" :alt="authStore.user?.full_name"></v-img>
              </v-avatar>
              {{ authStore.user?.full_name }}
            </v-chip>
          </template>

          <!-- 2. NỘI DUNG CỦA MENU (DANH SÁCH) -->
          <v-list>
            <v-list-item to="/profiles" prepend-icon="mdi-account-box-outline">
              <v-list-item-title>My Profiles</v-list-item-title>
            </v-list-item>
            <v-divider></v-divider>
            <v-list-item @click="handleLogout" prepend-icon="mdi-logout" base-color="error">
              <v-list-item-title>Logout</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </div>
      <!-- KẾT THÚC THAY ĐỔI: USER MENU -->
      
      <div v-else>
        <!-- Hiển thị khi chưa đăng nhập (không đổi) -->
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

    <VSnackbar v-model="notificationStore.visible"
      :color="color"
      :timeout="timeout"
      location="bottom right">
      {{ message }}
      <template>
        <VBtn variant="text" @click="notificationStore.visible = false">
          Close
        </VBtn>
      </template>
    </VSnackbar>
  </v-app>
</template>

<style scoped>
/* Thêm một chút style để tiêu đề trông đẹp hơn */
.v-app-bar-title .v-btn {
  text-transform: none; /* Bỏ viết hoa mặc định của nút */
  font-weight: bold;
}
</style>