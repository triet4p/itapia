<script lang="ts" setup>
import { RouterView } from 'vue-router';
import { VApp } from 'vuetify/components';
</script>

<template>
    <v-app>
        <v-app-bar title="ITAPIA - Intelligent and Transparent AI-Powered Personal Investment Assistant" elevation="2"></v-app-bar>
        <v-main>
            <RouterView />
        </v-main>
        <v-footer app>
            <span>&copy; {{ new Date().getFullYear() }} - ITAPIA Project</span>
        </v-footer>
    </v-app>
</template>

<style scoped>
</style>