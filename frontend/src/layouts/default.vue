<script lang="ts" setup>
import { RouterView } from 'vue-router';
import { VApp } from 'vuetify/components';
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

      <VBtn to="/login" variant="outlined">
        <template v-slot:prepend>
          <VIcon>mdi-login</VIcon>
        </template>
        Login
      </VBtn>
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