<script setup lang="ts">
import { useNotificationStore } from '@/stores/notificationStore';
import { ref, reactive, watch } from 'vue';
import { useRouter } from 'vue-router';

// --- STATE MANAGEMENT ---

const notificationStore = useNotificationStore();

type ProcessType = 'quick' | 'deep' | null;
const selectedProcess = ref<ProcessType>(null);

// Common data
const ticker = ref('');
const isNavigating = ref<boolean>(false);

// Option for quick check pipeline
const quickOptions = reactive({
  daily_analysis_type: 'medium',
  required_type: 'all',
  showKeyIndicators: true,
  showTopPatterns: true,
  selectedForecasts: [0, 1, 2], 
  showTopNews: true,
  showSummary: true,
});

// (Future) Option for deep dive
// const deepOptions = reactive({ ... });

const router = useRouter();

// --- LOGIC & METHODS ---

function startAnalysis() {
  if (!ticker.value) {
    notificationStore.showNotification({ message: 'Please input a ticker symbol.', color: 'error' });
    return;
  }
  if (!selectedProcess.value) {
    notificationStore.showNotification({ message: 'Please select an analysis process.', color: 'error' });
    return;
  }
  
  isNavigating.value = true;

  //Query params
  let query: Record<string, any> = {
    processType: selectedProcess.value,
  };

  if (selectedProcess.value === 'quick') {
    query = {
      ...query,
      daily_analysis_type: quickOptions.daily_analysis_type,
      required_type: quickOptions.required_type,
      showKeyIndicators: quickOptions.showKeyIndicators,
      showTopPatterns: quickOptions.showTopPatterns,
      // Convert forecasts Array to string to use in URL
      forecasts: quickOptions.selectedForecasts.join(','),
      showTopNews: quickOptions.showTopNews,
      showSummary: quickOptions.showSummary
    };
  } else if (selectedProcess.value === 'deep') {
    
  }
  
  // Navigate to result page
  router.push({
    name: '/analysis/[ticker]',
    params: { ticker: ticker.value.toUpperCase() },
    query: query,
  });
}

// Watch to reset if need
watch(selectedProcess, (newValue, oldValue) => {
  console.log(`Changed from ${oldValue} process to ${newValue} process`);
});

</script>

<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" md="10" lg="8">
        <h1 class="text-h4 text-center mb-6">ITAPIA Analysis</h1>

        <v-card class="pa-4" elevation="2">
          <!-- BASIC INFORMATION -->
          <v-card-title>Basic Information</v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="ticker"
                  label="Mã Cổ phiếu"
                  placeholder="VD: FPT, AAPL"
                  variant="outlined"
                  clearable
                ></v-text-field>
              </v-col>
              <v-col cols="12" sm="6">
                <p class="font-weight-medium mb-2">Choose process:</p>
                <v-radio-group v-model="selectedProcess" inline>
                  <v-radio label="Quick Analysis" value="quick"></v-radio>
                  <v-radio label="Deep Analysis (Further)" value="deep" disabled></v-radio>
                </v-radio-group>
              </v-col>
            </v-row>
          </v-card-text>

          <v-divider class="my-4"></v-divider>

          <!-- OPTION FOR QUICK ANALYSIS -->
          <v-expand-transition>
            <div v-if="selectedProcess === 'quick'">
              <v-card-title>Quick Analysis Options</v-card-title>
              <v-card-text>
                <v-row>
                  <!-- Các tham số cho API -->
                  <v-col cols="12" sm="6">
                    <v-select
                      v-model="quickOptions.daily_analysis_type"
                      label="Daily time frame"
                      :items="['short', 'medium', 'long']"
                      variant="outlined"
                    ></v-select>
                  </v-col>
                  <v-col cols="12" sm="6">
                    <v-select
                      v-model="quickOptions.required_type"
                      label="Require analysis type"
                      :items="['daily', 'intraday', 'all']"
                      variant="outlined"
                    ></v-select>
                  </v-col>
                </v-row>
                
                <v-divider class="my-2"></v-divider>
                
                <!-- Các tùy chọn hiển thị trên Frontend -->
                <p class="font-weight-medium mb-2 mt-4">Components displayed in the report:</p>
                <v-row>
                  <v-col cols="12" sm="4">
                    <v-checkbox v-model="quickOptions.showKeyIndicators" label="Key Indicators"></v-checkbox>
                  </v-col>
                  <v-col cols="12" sm="4">
                    <v-checkbox v-model="quickOptions.showTopPatterns" label="Top Patterns"></v-checkbox>
                  </v-col>
                   <v-col cols="12" sm="4">
                    <v-checkbox v-model="quickOptions.showTopNews" label="Top News"></v-checkbox>
                  </v-col>
                   <v-col cols="12" sm="4">
                    <v-checkbox v-model="quickOptions.showSummary" label="Summary of News"></v-checkbox>
                  </v-col>
                </v-row>
                
                 <v-divider class="my-2"></v-divider>
                 
                <p class="font-weight-medium mb-2 mt-4">Forecasting Task to display:</p>
                 <v-checkbox v-model="quickOptions.selectedForecasts" label="Triple Barrier" :value="0"></v-checkbox>
                 <v-checkbox v-model="quickOptions.selectedForecasts" label="5-Days Distribution (Mid-term)" :value="1"></v-checkbox>
                 <v-checkbox v-model="quickOptions.selectedForecasts" label="20-Days Distribution (Long-term)" :value="2"></v-checkbox>
              </v-card-text>
            </div>
          </v-expand-transition>
          
          <!-- (Future) OPTION FOR DEEP DIVE -->
          <!-- <div v-if="selectedProcess === 'deep'"> ... </div> -->

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
              color="primary"
              size="large"
              @click="startAnalysis"
              :disabled="!selectedProcess || !ticker || isNavigating"
              :loading="isNavigating"
            >
              Run Analysis
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>