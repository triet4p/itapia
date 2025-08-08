<script lang="ts" setup>
import { useAuthStore } from '@/stores/authStore';
import { storeToRefs } from 'pinia';

const authStore = useAuthStore();
const { isLoading } = storeToRefs(authStore);

function handleLogin() {
  authStore.redirectToGoogle();
}
</script>

<template>
  <VContainer class="fill-height">
    <VRow justify="center" align="center">
      <VCol cols="12" sm="8" md="6" lg="4">
        <VCard class="pa-4" elevation="4">
          <VCardTitle class="text-center text-h5 mb-4">
            Login to ITAPIA
          </VCardTitle>

          <VCardText>
            <p class="text-center mb-6">
              Please log in using your Google account to access personalized features.
            </p>
            <VBtn block color="#db4437" size="large" @click="handleLogin" :loading="isLoading" :disabled="isLoading">
              <v-icon start>mdi-google</v-icon>
              Login with Google
            </VBtn>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>
  </VContainer>
</template>

<style scoped>
/* Thêm một chút style cho nút Google */
.v-btn {
  color: white !important;
}
</style>