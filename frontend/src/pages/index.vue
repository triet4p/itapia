<script lang="ts" setup>
import { useNotificationStore } from '@/stores/notificationStore';
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const tickerSym = ref('');
const router = useRouter();
const notificationStore = useNotificationStore();

function startQuickAnalysis() {
  if (tickerSym.value) {
    const upperTickerSym = tickerSym.value.toUpperCase();
    
    // Only push, the result page will use default value for query params
    router.push({
      name: '/analysis/[ticker]',
      params: { ticker: upperTickerSym },
    });
  } else {
    notificationStore.showNotification({
      message: 'Please input a valid ticker symbol',
      color: 'error'
    });
  }
}

// Route to Advanced analysis page
function goToAdvancedAnalysis() {
    router.push({ name: '/analysis/' }); 
}
</script>

<template>
  <v-container class="fill-height">
    <v-row justify="center" align="center">
      <v-col cols="12" md="8" lg="6">
        <v-card elevation="4" class="pa-4">
          <v-card-title class="text-center text-h5">
            Start Your First Quick Check
          </v-card-title>

          <v-card-text>
            <v-text-field
              label="Input Ticker Symbol (e.g., AAPL, FPT)"
              variant="outlined"
              v-model="tickerSym"
              @keydown.enter="startQuickAnalysis"
              class="mb-4"
            ></v-text-field>

            <v-btn 
              block 
              color="primary" 
              size="large" 
              @click="startQuickAnalysis"
            >
              Run Quick Analysis
            </v-btn>
          </v-card-text>
          
          <v-divider class="my-4"></v-divider>
          
          <v-card-actions class="justify-center">
            <!-- Button route to Advanced Analysis Page -->
            <v-btn 
              variant="text" 
              @click="goToAdvancedAnalysis"
            >
              Or go to Advanced Analysis
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
.text-h5 {
  font-weight: bold !important;
}
</style>