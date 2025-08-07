<!-- src/pages/auth/callback.vue -->
<script setup lang="ts">
import { onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/authStore';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

onMounted(async () => {
  // 1. Đọc token từ query parameter trên URL
  const token = route.query.token as string;

  if (token) {
  // 2. Nếu có token, gọi action trong store để xử lý
  await authStore.handleLoginSuccess(token);
  // 3. Sau khi xử lý xong, điều hướng về trang chủ
  router.push('/');
  } else {
  // Nếu không có token, có thể là lỗi. Điều hướng về trang login.
  console.error("No token found in callback URL");
  // TODO: Có thể thêm query param lỗi để hiển thị thông báo
  router.push('/login');
  }
});
</script>

<template>
  <!-- Giao diện cực kỳ đơn giản, chỉ hiển thị khi đang xử lý -->
  <v-container class="fill-height">
  <v-row justify="center" align="center">
    <div class="text-center">
    <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
    <p class="mt-4">Finalizing authentication, please wait...</p>
    </div>
  </v-row>
  </v-container>
</template>