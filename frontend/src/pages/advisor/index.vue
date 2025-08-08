<script setup lang="ts">
import { useNotificationStore } from '@/stores/notificationStore';
import { ref } from 'vue';
import { useRouter } from 'vue-router';

// --- STATE MANAGEMENT ---
type ProcessType = 'quick' | 'deep' | null;
const selectedProcess = ref<ProcessType>('quick'); // Mặc định là 'quick'
const ticker = ref('');

const router = useRouter();
const notificationStore = useNotificationStore();

// --- LOGIC & METHODS ---
function startAdvisory() {
  if (!ticker.value) {
    notificationStore.showNotification({
      message: 'Please input a ticker symbol.',
      color: 'error'
    })
    return;
  }
  if (!selectedProcess.value) {
    notificationStore.showNotification({
      message: 'Please select an advisory process.',
      color: 'error'
    })
    return;
  }

  // Đối với Advisor, chúng ta chỉ cần truyền loại quy trình
  const query = {
    processType: selectedProcess.value,
  };

  // Điều hướng đến trang kết quả Advisor
  router.push({
    name: '/advisor/[ticker]',
    params: { ticker: ticker.value.toUpperCase() },
    query: query,
  });
}
</script>

<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" md="10" lg="8">
        <h1 class="text-h4 text-center mb-6">ITAPIA Advisor</h1>

        <v-card class="pa-4" elevation="2">
          <v-card-title>Configuration</v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="ticker"
                  label="Ticker Symbol"
                  placeholder="e.g., FPT, AAPL"
                  variant="outlined"
                  clearable
                ></v-text-field>
              </v-col>
              <v-col cols="12" sm="6">
                <p class="font-weight-medium mb-2">Choose process:</p>
                <v-radio-group v-model="selectedProcess" inline>
                  <v-radio label="Quick Advisory" value="quick"></v-radio>
                  <v-radio label="Deep Advisory (Coming Soon)" value="deep" disabled></v-radio>
                </v-radio-group>
              </v-col>
            </v-row>
          </v-card-text>

          <!-- Quick Check không có tùy chọn gì thêm -->

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
              color="success"
              size="large"
              @click="startAdvisory"
              :disabled="!selectedProcess || !ticker"
            >
              Get Advisory
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>