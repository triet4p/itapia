<!-- src/pages/auth/callback.vue -->
<script setup lang="ts">
import { onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/authStore';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

onMounted(async () => {
  // 1. Read Token from query
  const token = route.query.token as string;

  if (token) {
    await authStore.handleLoginSuccess(token);
    router.push('/');
  } else {
    console.error("No token found in callback URL");
    // TODO: Can add error params to debug
    router.push('/login');
  }
});
</script>

<template>
  <v-container class="fill-height">
  <v-row justify="center" align="center">
    <div class="text-center">
    <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
    <p class="mt-4">Finalizing authentication, please wait...</p>
    </div>
  </v-row>
  </v-container>
</template>