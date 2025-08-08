Ok, giờ là lúc bạn giúp tôi review code frontend lần cuối xem đã ổn chưa

# Pages
- index.vue
```vue
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
    
    // Chỉ điều hướng mà không gửi bất kỳ query params nào
    // Trang kết quả sẽ tự động dùng giá trị mặc định
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

// Hàm mới để điều hướng đến trang phân tích nâng cao
function goToAdvancedAnalysis() {
    router.push({ name: '/analysis/' }); // Điều hướng đến /analysis
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
            <!-- Nút điều hướng đến trang nâng cao -->
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
```
- login.vue
```vue
<script lang="ts" setup>
import { useAuthStore } from '@/stores/authStore';

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
```
- analysis/index.vue
```vue
<script setup lang="ts">
import { useNotificationStore } from '@/stores/notificationStore';
import { ref, reactive, watch } from 'vue';
import { useRouter } from 'vue-router';

// --- STATE MANAGEMENT ---

const notificationStore = useNotificationStore();

// Loại quy trình phân tích
type ProcessType = 'quick' | 'deep' | null;
const selectedProcess = ref<ProcessType>(null);

// Dữ liệu chung cho form
const ticker = ref('');
const isNavigating = ref<boolean>(false);

// Các tùy chọn cho Quick Analysis
const quickOptions = reactive({
  daily_analysis_type: 'medium',
  required_type: 'all',
  showKeyIndicators: true,
  showTopPatterns: true,
  // Dùng mảng để lưu các lựa chọn forecasting
  selectedForecasts: [0, 1, 2], // Mặc định chọn cả 3
  showTopNews: true,
  showSummary: true,
});

// (Tương lai) Các tùy chọn cho Deep Analysis
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

  // Tập hợp các query params
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
      // Chuyển mảng forecasting thành chuỗi để truyền qua URL
      forecasts: quickOptions.selectedForecasts.join(','),
      showTopNews: quickOptions.showTopNews,
      showSummary: quickOptions.showSummary
    };
  } else if (selectedProcess.value === 'deep') {
    // (Tương lai) Thêm logic cho Deep Dive ở đây
    // query = { ...query, ...deepOptions };
  }
  
  // Điều hướng đến trang kết quả
  router.push({
    name: '/analysis/[ticker]',
    params: { ticker: ticker.value.toUpperCase() },
    query: query,
  });
}

// Theo dõi sự thay đổi của quy trình để reset các tùy chọn nếu cần
watch(selectedProcess, (newValue, oldValue) => {
  console.log(`Đã chuyển từ quy trình ${oldValue} sang ${newValue}`);
  // Có thể thêm logic reset các form ở đây trong tương lai
});

</script>

<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" md="10" lg="8">
        <h1 class="text-h4 text-center mb-6">ITAPIA Analysis</h1>

        <v-card class="pa-4" elevation="2">
          <!-- BƯỚC 1: CÁC THÔNG TIN CƠ BẢN -->
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
                <!-- Sử dụng v-radio-group để chọn 1 trong 2 quy trình -->
                <p class="font-weight-medium mb-2">Choose process:</p>
                <v-radio-group v-model="selectedProcess" inline>
                  <v-radio label="Quick Analysis" value="quick"></v-radio>
                  <v-radio label="Deep Analysis (Further)" value="deep" disabled></v-radio>
                </v-radio-group>
              </v-col>
            </v-row>
          </v-card-text>

          <v-divider class="my-4"></v-divider>

          <!-- BƯỚC 2: CÁC TÙY CHỌN CHO QUICK ANALYSIS -->
          <!-- Dùng v-expand-transition và v-if để chỉ hiện khi đã chọn 'quick' -->
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
          
          <!-- (Tương lai) Tùy chọn cho Deep Dive sẽ nằm ở đây -->
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
```
- analysis/[ticker].vue
```vue
<script lang="ts" setup>
import { onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import { useAnalysisStore } from '@/stores/analysisStore';

const showFullJson = ref<boolean>(false);

// --- Store
const analysisStore = useAnalysisStore();
const { report, explaination, isLoading, error } = storeToRefs(analysisStore);

// --- ROUTE & PARAMS ---
const route = useRoute('/analysis/[ticker]');
const ticker = route.params.ticker as string;

// --- HELPER FUNCTIONS FOR FORMATTING ---

/**
 * Chuyển đổi kết quả dự báo Triple Barrier thành chuỗi dễ đọc.
 */
function formatTripleBarrierPrediction(prediction: number): string {
  if (prediction === 1) return 'Take-Profit Hit';
  if (prediction === -1) return 'Stop-Loss Hit';
  if (prediction === 0) return 'No Barrier Hit';
  return 'Unknown';
}

/**
 * Chuyển đổi tên target của bài toán phân phối thành dạng đẹp hơn.
 * VD: 'target_mean_pct_5d' -> 'Mean'
 */
function formatDistributionTargetName(target: string): string {
  const parts = target.split('_');
  if (parts.length > 1) {
    const descriptivePart = parts[1];
    return descriptivePart.charAt(0).toUpperCase() + descriptivePart.slice(1);
  }
  return target; // Trả về nguyên bản nếu không đúng định dạng
}

// --- LIFECYCLE HOOK ---
onMounted(() => {
  analysisStore.fetchReport(ticker, route.query);
});

// Đọc và xử lý tất cả các query params từ URL
const displayOptions = computed(() => {
  const query = route.query;
  return {
    daily_analysis_type: (query.daily_analysis_type || 'medium') as 'short' | 'medium' | 'long',
    required_type: (query.required_type || 'all') as 'daily' | 'intraday' | 'all',
    showKeyIndicators: query.showKeyIndicators !== 'false',
    showTopPatterns: query.showTopPatterns !== 'false',
    showTopNews: query.showTopNews !== 'false',
    showSummary: query.showSummary !== 'false', // Chỉ dành cho News Summary
    selectedForecasts: query.forecasts ? (query.forecasts as string).split(',').map(Number) : [0,1,2]
  };
});

// --- COMPUTED PROPERTIES ---
const keyIndicatorsList = computed(() => {
  if (!report.value?.technical_report.daily_report?.key_indicators) return [];
  const indicators = report.value.technical_report.daily_report.key_indicators;
  return Object.entries(indicators).map(([key, value]) => ({
    name: key.toUpperCase(),
    value: typeof value === 'number' ? value.toFixed(2) : 'Can not compute'
  }));
});

const topPatterns = computed(() => report.value?.technical_report.daily_report?.pattern_report.top_patterns?.slice(0, 3) || []);

const filteredForecasts = computed(() => {
  const allForecasts = report.value?.forecasting_report.forecasts || [];
  return allForecasts.filter((_, index) => displayOptions.value.selectedForecasts.includes(index));
});

// Computed property mới cho News Summary
const newsSummary = computed(() => report.value?.news_report.summary);

</script>

<template>
  <v-container>
    <!-- Giao diện Loading và Error -->
    <div v-if="isLoading" class="text-center pa-10">
      <v-progress-circular indeterminate color="primary" :size="70" :width="7"></v-progress-circular>
      <h2 class="mt-4">Analyzing {{ ticker }}...</h2>
      <p class="text-body-1">Please wait a moment while we gather and process the data.</p>
    </div>
    <v-alert type="error" v-else-if="error" title="Analysis Error" :text="error" variant="tonal"></v-alert>

    <!-- Giao diện hiển thị dữ liệu -->
    <div v-else-if="report">
      <h1 class="text-h4 mb-2">Analysis Report: {{ ticker }}</h1>
      <p class="text-subtitle-1 mb-6">Generated at {{ new Date(report.generated_at_utc).toLocaleString('en-GB') }}</p>

      <v-row>
        <!-- CỘT BÊN TRÁI: GIẢI THÍCH VÀ CÁC BÁO CÁO CHÍNH -->
        <v-col cols="12" md="7">
          <!-- 1. BẢN TÓM TẮT GIẢI THÍCH (LUÔN HIỂN THỊ) -->
          <v-card class="mb-6">
            <v-card-title>Explanation Summary</v-card-title>
            <v-card-text>
              <pre class="explanation-text">{{ explaination }}</pre>
            </v-card-text>
          </v-card>

        </v-col>

        <!-- CỘT BÊN PHẢI: THÔNG TIN NHANH -->
        <v-col cols="12" md="5">
          <!-- 4. CÁC CHỈ SỐ CHÍNH (HIỂN THỊ CÓ ĐIỀU KIỆN) -->
          <v-card v-if="displayOptions.showKeyIndicators" class="mb-6">
            <v-card-title>Key Indicators</v-card-title>
            <!-- (Code hiển thị key indicators giữ nguyên) -->
            <v-list lines="one" density="compact">
              <template v-for="(indicator, index) in keyIndicatorsList" :key="indicator.name">
                <v-list-item v-if="indicator" :title="indicator.name" :subtitle="indicator.value"></v-list-item>
                <v-divider v-if="index < keyIndicatorsList.length - 1"></v-divider>
              </template>
            </v-list>
          </v-card>

          <!-- 5. CÁC MẪU HÌNH (HIỂN THỊ CÓ ĐIỀU KIỆN) -->
          <v-card v-if="displayOptions.showTopPatterns && topPatterns.length > 0" class="mb-6">
            <v-card-title>Top Patterns</v-card-title>
            <!-- (Code hiển thị patterns giữ nguyên) -->
            <v-list lines="one" density="compact">
              <template v-for="(pattern, index) in topPatterns" :key="pattern.name">
                <v-list-item :title="pattern.name" :subtitle="pattern.sentiment" :class="`sentiment-${pattern.sentiment}`"></v-list-item>
                <v-divider v-if="index < topPatterns.length - 1"></v-divider>
              </template>
            </v-list>
          </v-card>

          <!-- 2. BÁO CÁO DỰ BÁO (HIỂN THỊ CÓ ĐIỀU KIỆN) -->
          <v-card v-if="filteredForecasts.length > 0" class="mb-6">
            <v-card-title>Forecasting Report</v-card-title>
            <!-- (Code hiển thị forecasting giữ nguyên) -->
            <v-list>
              <template v-for="(task, index) in filteredForecasts" :key="task.task_name">
                <v-list-item class="by-grey-lighten-4">
                  <v-list-item-title class="font-weight-bold text-subtitle-1">{{ task.task_name }}</v-list-item-title>
                  <v-list-item-subtitle>
                    <v-chip size="small" class="mr-2" label>Horizon: {{ task.task_metadata.horizon }} days</v-chip>
                    <v-chip v-if="task.task_metadata.problem_id === 'triple-barrier'" size="small" class="mr-2" label>TP: {{ (task.task_metadata.tp_pct * 100).toFixed(1) }}%</v-chip>
                    <v-chip v-if="task.task_metadata.problem_id === 'triple-barrier'" size="small" label>SL: {{ (task.task_metadata.sl_pct * 100).toFixed(1) }}%</v-chip>
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list density="compact" class="ml-4">
                  <v-list-item v-for="(targetName, targetIndex) in task.task_metadata.targets" :key="targetName">
                    <template v-if="task.task_metadata.problem_id === 'triple-barrier'">
                      <v-list-item-title>Predicted: </v-list-item-title>
                      <span class="font-weight-medium">{{ formatTripleBarrierPrediction(task.prediction[targetIndex]) }}</span>
                    </template>
                    <template v-else-if="task.task_metadata.problem_id === 'ndays-distribution'">
                      <v-list-item-title>{{ formatDistributionTargetName(targetName) }} </v-list-item-title>
                      <span class="font-weight-medium">{{ (task.prediction[targetIndex]).toFixed(2) }}%</span>
                    </template>
                  </v-list-item>
                </v-list>
                <v-divider v-if="index < filteredForecasts.length - 1"></v-divider>
              </template>
            </v-list>
          </v-card>

          <!-- 3. TÓM TẮT TIN TỨC (HIỂN THỊ CÓ ĐIỀU KIỆN) -->
          <v-card v-if="displayOptions.showSummary && newsSummary" class="mb-6">
            <v-card-title>News Analysis Summary</v-card-title>
             <v-list density="compact">
                <v-list-item title="Positive Sentiment" :subtitle="newsSummary.num_positive_sentiment"></v-list-item>
                <v-list-item title="Negative Sentiment" :subtitle="newsSummary.num_negative_sentiment"></v-list-item>
                <v-list-item title="High Impact News" :subtitle="newsSummary.num_high_impact"></v-list-item>
             </v-list>
          </v-card>
        </v-col>
      </v-row>
      
      <!-- KHU VỰC JSON ĐẦY ĐỦ -->
      <v-card class="mt-6">
        <!-- (Code không đổi) -->
        <v-card-actions>
          <v-btn @click="showFullJson = !showFullJson">
            {{ showFullJson ? 'Hide' : 'Show' }} Full JSON Report
          </v-btn>
        </v-card-actions>
        <v-expand-transition>
          <div v-show="showFullJson">
            <v-divider></v-divider>
            <v-card-text>
              <pre class="json-dump"><code>{{ JSON.stringify(report, null, 2) }}</code></pre>
            </v-card-text>
          </div>
        </v-expand-transition>
      </v-card>
    </div>
  </v-container>
</template>

<style scoped>
/* (Style không đổi) */
.explanation-text {
  background-color: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: 'Courier New', Courier, monospace;
  color: #333;
}
.json-dump {
  background-color: #2d2d2d;
  color: #f8f8f2;
  padding: 16px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: 'Courier New', Courier, monospace;
}
.sentiment-bull { color: #4CAF50; }
.sentiment-bear { color: #F44336; }
.sentiment-neutral { color: #9E9E9E; }
</style>
```
- advisor/index.vue
```vue
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
```
- advisor/[ticker].vue
```vue
<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import type { components } from '@/types/api';
import { useAdvisorStore } from '@/stores/advisorStore';

const showFullJson = ref<boolean>(false);

const advisorStore = useAdvisorStore();
const { report, explaination, isLoading, error } = storeToRefs(advisorStore);

// --- ROUTE & PARAMS ---
const route = useRoute('/advisor/[ticker]');
const ticker = route.params.ticker as string;

// TODO: Sau này user_id sẽ được lấy từ Pinia authStore
const userId = ref(''); // Placeholder

// --- HELPER FUNCTIONS ---

/**
 * Xác định màu sắc cho nhãn dựa trên nội dung của nó.
 */
function getLabelColor(label: string): string {
  label = label.toUpperCase()
  if (label.includes('BUY') || label.includes('POSITIVE') 
      || label.includes('STRONG') || label.includes('INTERESTING')
      || label.includes('ACCUMULATE')) {
    return 'success'; // Xanh lá
  }
  if (label.includes('SELL') || label.includes('NEGATIVE') 
      || label.includes('RISK_HIGH') || label.includes('RISK_HIGH')
      || label.includes('AVOID') || label.includes('REDUCE')) {
    return 'error'; // Đỏ
  }
  return 'grey'; // Xám cho trung tính
}

// --- LIFECYCLE HOOK ---
onMounted(() => {
  advisorStore.fetchReport(ticker, userId.value);
});
</script>

<template>
  <v-container>
    <!-- Giao diện Loading và Error -->
    <div v-if="isLoading" class="text-center pa-10">
      <v-progress-circular indeterminate color="primary" :size="70" :width="7"></v-progress-circular>
      <h2 class="mt-4">Generating advisory for {{ ticker }}...</h2>
    </div>
    <v-alert type="error" v-else-if="error" title="Advisory Error" :text="error" variant="tonal"></v-alert>

    <!-- Giao diện hiển thị dữ liệu -->
    <div v-else-if="report">
      <h1 class="text-h4 mb-2">Advisory Report: {{ report.ticker }}</h1>
      <p class="text-subtitle-1 mb-6">Generated at {{ new Date(report.generated_at_utc).toLocaleString('en-GB') }}</p>

      <v-row>
        <!-- CỘT BÊN TRÁI: GIẢI THÍCH CHI TIẾT -->
        <v-col cols="12" md="7">
          <v-card class="mb-6">
            <v-card-title>Explanation Summary</v-card-title>
            <v-card-text>
              <pre class="explanation-text">{{ explaination }}</pre>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- CỘT BÊN PHẢI: KẾT LUẬN CHÍNH -->
        <v-col cols="12" md="5">
          <!-- Card cho Quyết định -->
          <v-card class="mb-6">
            <v-list-item>
              <template v-slot:prepend>
                <v-icon color="blue">mdi-lightbulb-on-outline</v-icon>
              </template>
              <v-list-item-title class="text-h6">Decision</v-list-item-title>
              <v-list-item-subtitle>Final Score: {{ report.final_decision.final_score.toFixed(2) }}</v-list-item-subtitle>
            </v-list-item>
            <v-card-text>
              <v-chip :color="getLabelColor(report.final_decision.label)" class="wrap-chip-text">
                {{ report.final_decision.final_recommend.replace("Threshold match is THRESHOLD_DECISION_", "").replace(", which mean ", ": ") }}
              </v-chip>
            </v-card-text>
            <v-expansion-panels variant="accordion">
              <v-expansion-panel title="Triggered Rules">
                <v-expansion-panel-text>
                  <v-list density="compact">
                    <v-list-item
                      v-for="rule in report.final_decision.triggered_rules"
                      :key="rule.rule_id"
                      :title="rule.name"
                    >
                      <!-- Sử dụng slot mặc định để chèn nội dung tùy chỉnh -->
                      <div>
                        <div class="text-caption text-grey-darken-1 text-h5">{{ rule.rule_id }}</div>
                        <div class="font-weight-small">Score: {{ rule.score.toFixed(2) }}</div>
                      </div>
                    </v-list-item>
                  </v-list>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card>
          
          <!-- Card cho Rủi ro -->
          <v-card class="mb-6">
             <v-list-item>
              <template v-slot:prepend>
                <v-icon color="orange">mdi-shield-alert-outline</v-icon>
              </template>
              <v-list-item-title class="text-h6">Risk Level</v-list-item-title>
              <v-list-item-subtitle>Final Score: {{ report.final_risk.final_score.toFixed(2) }}</v-list-item-subtitle>
            </v-list-item>
            <v-card-text>
              <v-chip :color="getLabelColor(report.final_risk.label)" class="wrap-chip-text">
                {{ report.final_risk.final_recommend.replace("Threshold match is THRESHOLD_RISK_", "").replace(", which mean ", ": ") }}
              </v-chip>
            </v-card-text>
            <v-expansion-panels variant="accordion">
              <v-expansion-panel title="Triggered Rules">
                <v-expansion-panel-text>
                  <v-list density="compact">
                    <v-list-item
                      v-for="rule in report.final_risk.triggered_rules"
                      :key="rule.rule_id"
                      :title="rule.name"
                    >
                      <!-- Sử dụng slot mặc định để chèn nội dung tùy chỉnh -->
                      <div>
                        <div class="text-caption text-grey-darken-1 text-h5">{{ rule.rule_id }}</div>
                        <div class="font-weight-small">Score: {{ rule.score.toFixed(2) }}</div>
                      </div>
                    </v-list-item>
                  </v-list>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card>
          
          <!-- Card cho Cơ hội -->
          <v-card>
             <v-list-item>
              <template v-slot:prepend>
                <v-icon color="green">mdi-trending-up</v-icon>
              </template>
              <v-list-item-title class="text-h6">Opportunity Rating</v-list-item-title>
              <v-list-item-subtitle>Final Score: {{ report.final_opportunity.final_score.toFixed(2) }}</v-list-item-subtitle>
            </v-list-item>
            <v-card-text>
              <v-chip :color="getLabelColor(report.final_opportunity.label)" class="wrap-chip-text">
                {{ report.final_opportunity.final_recommend.replace("Threshold match is THRESHOLD_OPP_RATING_", "").replace(", which mean ", ": ") }}
              </v-chip>
            </v-card-text>
            <v-expansion-panels variant="accordion">
              <v-expansion-panel title="Triggered Rules">
                <v-expansion-panel-text>
                  <v-list density="compact">
                    <v-list-item
                      v-for="rule in report.final_opportunity.triggered_rules"
                      :key="rule.rule_id"
                      :title="rule.name"
                    >
                      <!-- Sử dụng slot mặc định để chèn nội dung tùy chỉnh -->
                      <div>
                        <div class="text-caption text-grey-darken-1 text-h5">{{ rule.rule_id }}</div>
                        <div class="font-weight-small">Score: {{ rule.score.toFixed(2) }}</div>
                      </div>
                    </v-list-item>
                  </v-list>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card>

        </v-col>
      </v-row>

      <!-- KHU VỰC JSON ĐẦY ĐỦ -->
      <v-card class="mt-6">
        <!-- (Code không đổi) -->
        <v-card-actions>
          <v-btn @click="showFullJson = !showFullJson">
            {{ showFullJson ? 'Hide' : 'Show' }} Full JSON Report
          </v-btn>
        </v-card-actions>
        <v-expand-transition>
          <div v-show="showFullJson">
            <v-divider></v-divider>
            <v-card-text>
              <pre class="json-dump"><code>{{ JSON.stringify(report, null, 2) }}</code></pre>
            </v-card-text>
          </div>
        </v-expand-transition>
      </v-card>
    </div>
  </v-container>
</template>

<style scoped>
.explanation-text {
  background-color: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'Courier New', Courier, monospace;
  color: #333;
}
.wrap-chip-text {
  height: auto !important; /* !important để ghi đè style mặc định của Vuetify */
  white-space: normal;
  padding-top: 4px;
  padding-bottom: 4px;
}
</style>
```
- rules/index.vue
```vue
<!-- src/pages/rules/index.vue -->
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import type { components } from '@/types/api';
import { SEMANTIC_TYPE_OPTIONS } from '@/constants/api';
import { VDataTable } from 'vuetify/components';
import { useRulesStore } from '@/stores/rulesStore';

// --- TYPE DEFINITIONS ---
type RuleResponse = components['schemas']['RuleResponse'];
type SemanticType = components['schemas']['SemanticType'];
type ReadonlyHeaders = VDataTable['$props']['headers'];

// --- STORE ---
const rulesStore = useRulesStore();
const { rulesList, isLoadingList, error } = storeToRefs(rulesStore);

// --- REACTIVE STATE ---
const search = ref('');
const selectedPurpose = ref<SemanticType>('ANY');

// --- DATA TABLE HEADERS ---
const headers: ReadonlyHeaders = [
  { 
    title: 'Rule ID', 
    key: 'rule_id',
    // Sử dụng `cellProps` để thêm class vào các ô <td>
    cellProps: { class: 'rule-id-col' },
    align: 'start' 
  },
  { 
    title: 'Name', 
    key: 'name', 
    cellProps: { class: 'name-col' },
    align: 'start' 
  },
  { 
    title: 'Purpose', 
    key: 'purpose', 
    cellProps: { class: 'purpose-col' },
    align: 'start' 
  },
  { 
    title: 'Version', 
    key: 'version', 
    cellProps: { class: 'version-col' },
    align: 'center' 
  },
  { 
    title: 'Active', 
    key: 'is_active', 
    cellProps: { class: 'active-col' },
    align: 'center' 
  },
  { 
    title: 'Created At', 
    key: 'created_at_ts', 
    cellProps: { class: 'created-at-col' },
    align: 'start' 
  },
  { 
    title: 'Actions', 
    key: 'actions', 
    cellProps: { class: 'actions-col' },
    sortable: false, 
    align: 'end' 
  },
];

const router = useRouter();
// --- HELPERS ---
function formatTimestamp(ts: number): string {
  return new Date(ts * 1000).toLocaleString('vn-VN');
}

function viewRuleDetails(item: RuleResponse) {
  router.push(`/rules/${item.rule_id}`);
}

// --- LIFECYCLE & WATCHERS ---
onMounted(() => {
  rulesStore.fetchRules(selectedPurpose.value);
});
</script>

<template>
  <v-container>
    <h1 class="text-h4 mb-4">Rules Library</h1>
    <v-alert v-if="error" type="error" class="mb-4">{{ error }}</v-alert>
    
    <v-card>
      <v-card-title>
        <v-row align="center">
          <v-col cols="12" md="4">
            <v-select
              v-model="selectedPurpose"
              :items="SEMANTIC_TYPE_OPTIONS"
              label="Filter by Purpose"
              density="compact"
              variant="outlined"
              hide-details
              @update:modelValue="rulesStore.fetchRules"
            ></v-select>
          </v-col>
          <v-col cols="12" md="8">
            <v-text-field
              v-model="search"
              append-inner-icon="mdi-magnify"
              label="Search"
              single-line
              hide-details
              density="compact"
              variant="outlined"
            ></v-text-field>
          </v-col>
        </v-row>
      </v-card-title>

      <v-data-table
        :headers="headers"
        :items="rulesList"
        :search="search"
        :loading="isLoadingList"
        items-per-page="15"
      >
        <template v-slot:item.is_active="{ value }">
          <v-chip :color="value ? 'success' : 'grey'" size="small">
            {{ value ? 'Active' : 'Inactive' }}
          </v-chip>
        </template>
        <template v-slot:item.created_at_ts="{ value }">
          {{ formatTimestamp(value) }}
        </template>
        <template v-slot:item.actions="{ item }">
          <v-btn
            variant="text"
            icon="mdi-magnify-plus-outline"
            @click="viewRuleDetails(item)"
          ></v-btn>
        </template>
      </v-data-table>
    </v-card>
  </v-container>
</template>

<style scoped>
/* Dùng :deep() để style các phần tử được tạo ra bởi component v-data-table */

/* Cột Rule ID: Rộng, nhưng có thể co lại nếu cần */
:deep(.rule-id-col) {
  min-width: 280px !important;
}

/* Cột Name: Linh hoạt, sẽ chiếm phần lớn không gian còn lại */
:deep(.name-col) {
  min-width: 300px !important;
}

/* Cột Purpose: Rộng vừa phải */
:deep(.purpose-col) {
  min-width: 180px !important;
}

/* Cột Version và Active: Hẹp, cố định */
:deep(.version-col),
:deep(.active-col) {
  width: 100px !important;
}

/* Cột Created At: Rộng vừa phải */
:deep(.created-at-col) {
  min-width: 180px !important;
}

/* Cột Actions: Hẹp, cố định */
:deep(.actions-col) {
  width: 100px !important;
}
</style>
```
- rules/[rule_id].vue
```vue
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import type { components } from '@/types/api';
import TreeNode from '@/components/TreeNode.vue';
import { useRulesStore } from '@/stores/rulesStore';

// --- STORE ---
const rulesStore = useRulesStore();
const { currentRule, nodeDictionary, isLoadingDetails, error } = storeToRefs(rulesStore);

// --- TYPE DEFINITIONS ---
type NodeSpec = components['schemas']['NodeResponse'];

// --- REACTIVE STATE ---
const dialogVisible = ref(false);
const selectedNodeDetails = ref<NodeSpec | null>(null);

// --- ROUTE & PARAMS ---
const route = useRoute('/rules/[rule_id]');
const ruleId = route.params.rule_id as string;

// --- DATA FETCHING ---
async function fetchData() {
  try {
    isLoadingDetails.value = true;
    const rulePromise = axios.get(`http://localhost:8000/api/v1/rules/${ruleId}/explain`);
    const nodesPromise = axios.get('http://localhost:8000/api/v1/rules/nodes');
    
    const [ruleResponse, nodesResponse] = await Promise.all([rulePromise, nodesPromise]);
    
    currentRule.value = ruleResponse.data;
    nodeDictionary.value = nodesResponse.data;
  } catch (e: any) {
    error.value = `Could not fetch data for rule ${ruleId}. Error: ${e.message}`;
  } finally {
    isLoadingDetails.value = false;
  }
}

// --- LOGIC ---
function handleNodeClick(nodeName: string) {
  const foundNode = nodeDictionary.value.find(n => n.node_name === nodeName);
  if (foundNode) {
    selectedNodeDetails.value = foundNode;
    dialogVisible.value = true;
  }
}

// --- LIFECYCLE HOOK ---
onMounted(() => {
  fetchData();
});
</script>

<template>
  <v-container>
    <div v-if="isLoadingDetails" class="text-center pa-10">
      <v-progress-circular indeterminate color="primary"></v-progress-circular>
    </div>
    <v-alert v-else-if="error" type="error">{{ error }}</v-alert>

    <div v-else-if="currentRule">
      <h1 class="text-h4">{{ currentRule.name }}</h1>
      <p class="text-subtitle-1 mb-4">{{ currentRule.rule_id }}</p>

      <v-row>
        <v-col cols="12" md="4">
          <v-card>
            <v-card-title>Metadata</v-card-title>
            <v-list density="compact">
              <v-list-item title="Purpose" :subtitle="currentRule.purpose"></v-list-item>
              <v-list-item title="Version" :subtitle="currentRule.version"></v-list-item>
              <v-list-item title="Status">
                <template v-slot:subtitle>
                  <v-chip :color="currentRule.is_active ? 'success' : 'grey'" size="small">
                    {{ currentRule.is_active ? 'Active' : 'Inactive' }}
                  </v-chip>
                </template>
              </v-list-item>
              <v-list-item title="Created At" :subtitle="new Date(currentRule.created_at_ts * 1000).toLocaleString('en-GB')"></v-list-item>
            </v-list>
          </v-card>
        </v-col>
        <v-col cols="12" md="8">
          <v-card>
            <v-card-title>Rule Tree</v-card-title>
            <v-card-text>
              <TreeNode :node="currentRule.root" :depth="0" @node-click="handleNodeClick" />
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
      
      <v-card class="mt-6">
        <v-card-title>Explanation</v-card-title>
        <v-card-text>
          <p class="explanation-text">{{ currentRule.explain }}</p>
        </v-card-text>
      </v-card>

      <v-btn to="/rules" prepend-icon="mdi-arrow-left" class="mt-6">Back to Library</v-btn>
    </div>

    <!-- Dialog for Node Details -->
    <v-dialog v-model="dialogVisible" max-width="600px">
      <v-card v-if="selectedNodeDetails">
        <v-card-title class="d-flex align-center">
          <span class="text-h5">{{ selectedNodeDetails.node_name }}</span>
          <v-chip size="small" class="ml-4">{{ selectedNodeDetails.node_type }}</v-chip>
        </v-card-title>
        <v-card-text>
          <p class="mb-4">{{ selectedNodeDetails.description }}</p>
          <v-divider></v-divider>
          <v-list density="compact">
            <v-list-item title="Return Type" :subtitle="selectedNodeDetails.return_type"></v-list-item>
            <v-list-item v-if="selectedNodeDetails.args_type" title="Argument Types">
              <template v-slot:subtitle>
                <v-chip v-for="arg in selectedNodeDetails.args_type" :key="arg" size="small" class="mr-1">{{ arg }}</v-chip>
              </template>
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" text @click="dialogVisible = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </v-container>
</template>

<style scoped>
.explanation-text {
  background-color: #f5f5f5;
  padding: 1rem;
  border-radius: 4px;
  color: #333;
  font-family: monospace;
  white-space: pre-wrap;
}
</style>
```
- profiles/index.vue
```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { useProfileStore } from '@/stores/profilesStore';
import type { components } from '@/types/api';

// --- TYPE DEFINITIONS ---
type ProfileCreate = components['schemas']['ProfileCreateRequest'];
type Profile = components['schemas']['ProfileResponse'];

// --- STORE & STATE ---
const profileStore = useProfileStore();
const { profiles, isLoadingList, error } = storeToRefs(profileStore);

const dialogCreate = ref(false);
const wizardStep = ref(1);
const totalWizardSteps = 6; // Tổng số bước để quản lý nút Next/Create

// --- FORM STATE ---
// Dữ liệu mặc định cho form tạo mới
const defaultFormState = (): ProfileCreate => ({
  profile_name: '',
  description: '',
  risk_tolerance: { risk_appetite: 'moderate', loss_reaction: 'hold_and_wait' },
  invest_goal: { primary_goal: 'capital_growth', investment_horizon: 'mid_term', expected_annual_return_pct: 15 },
  knowledge_exp: { investment_knowledge: 'intermediate', years_of_experience: 3 },
  capital_income: { initial_capital: 10000, income_dependency: 'low' },
  personal_prefer: { preferred_sectors: [], excluded_sectors: [], ethical_investing: false },
  use_in_advisor: true,
  is_default: false,
});

const newProfileForm = ref<ProfileCreate>(defaultFormState());

// --- LIFECYCLE HOOK ---
onMounted(() => {
  profileStore.fetchProfiles();
});

// --- METHODS ---
function openCreateDialog() {
  // Reset form về trạng thái mặc định mỗi khi mở dialog
  newProfileForm.value = defaultFormState();
  wizardStep.value = 1;
  dialogCreate.value = true;
}

async function handleCreateProfile() {
  const success = await profileStore.createProfile(newProfileForm.value);
  if (success) {
    dialogCreate.value = false;
    // Không cần reset form ở đây vì đã reset khi mở
  } else {
    // TODO: Hiển thị lỗi bằng snackbar
    alert('Creation failed! Please check the console for details.');
  }
}
</script>

<template>
  <v-container>
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h4">My Investment Profiles</h1>
      <v-btn color="primary" @click="openCreateDialog" prepend-icon="mdi-plus" :disabled="profiles.length >= 10">
        New Profile
      </v-btn>
    </div>
    
    <v-alert v-if="error" type="error" class="mb-4" closable>{{ error }}</v-alert>

    <v-card :loading="isLoadingList">
      <v-list lines="two">
        <v-list-subheader>Your Profiles ({{ profiles.length }}/10)</v-list-subheader>
        <v-list-item
          v-if="profiles.length > 0"
          v-for="profile in profiles"
          :key="profile.profile_id"
          :title="profile.profile_name"
          :subtitle="profile.description"
          :to="`/profiles/${profile.profile_id}`"
        >
          <template v-slot:append>
            <v-chip v-if="profile.is_default" color="success" size="small" label>Default</v-chip>
            <v-icon>mdi-chevron-right</v-icon>
          </template>
        </v-list-item>
        <v-list-item v-else-if="!isLoadingList">
          <v-list-item-title>No profiles found.</v-list-item-title>
          <v-list-item-subtitle>Click "New Profile" to get started.</v-list-item-subtitle>
        </v-list-item>
      </v-list>
    </v-card>

    <!-- DIALOG TẠO MỚI DẠNG WIZARD -->
    <v-dialog v-model="dialogCreate" persistent max-width="800px">
      <v-card>
        <v-card-title>
          <span class="text-h5">Create New Profile (Step {{ wizardStep }}/{{ totalWizardSteps }})</span>
        </v-card-title>
        
        <v-card-text class="dialog-scrollable-content">
          <v-window v-model="wizardStep">
            <!-- BƯỚC 1: Basic Info -->
            <v-window-item :value="1">
              <p class="text-h6 mb-4">Basic Info</p>
              <v-text-field v-model="newProfileForm.profile_name" label="Profile Name" hint="e.g., Long-term Growth, Safe Retirement" persistent-hint></v-text-field>
              <v-textarea v-model="newProfileForm.description" label="Description" hint="Describe the strategy for this profile" persistent-hint class="mt-4"></v-textarea>
            </v-window-item>
            
            <!-- BƯỚC 2: Risk Tolerance -->
            <v-window-item :value="2">
              <p class="text-h6 mb-4">Risk Tolerance</p>
              <p>1. What is your overall risk tolerance?</p>
              <v-radio-group v-model="newProfileForm.risk_tolerance.risk_appetite">
                <v-radio label="Very Conservative" value="very_conservative"></v-radio>
                <v-radio label="Conservative" value="conservative"></v-radio>
                <v-radio label="Moderate" value="moderate"></v-radio>
                <v-radio label="Aggressive" value="aggressive"></v-radio>
                <v-radio label="Very Aggressive" value="very_aggressive"></v-radio>
              </v-radio-group>
              <p class="mt-4">2. Your reaction to a significant market drop?</p>
              <v-radio-group v-model="newProfileForm.risk_tolerance.loss_reaction">
                  <v-radio label="Panic and sell immediately" value="panic_sell"></v-radio>
                  <v-radio label="Reduce exposure" value="reduce_exposure"></v-radio>
                  <v-radio label="Hold and wait" value="hold_and_wait"></v-radio>
                  <v-radio label="See it as a buying opportunity" value="buy_the_dip"></v-radio>
              </v-radio-group>
            </v-window-item>
            
            <!-- BƯỚC 3: Investment Goals -->
            <v-window-item :value="3">
              <p class="text-h6 mb-4">Investment Goals</p>
               <p>1. What is your primary investment goal?</p>
               <v-radio-group v-model="newProfileForm.invest_goal.primary_goal">
                 <v-radio label="Capital Preservation (Safe)" value="capital_preservation"></v-radio>
                 <v-radio label="Income Generation (Dividends)" value="income_generation"></v-radio>
                 <v-radio label="Capital Growth (Balanced)" value="capital_growth"></v-radio>
                 <v-radio label="Speculation (High Risk/Reward)" value="speculation"></v-radio>
               </v-radio-group>
               <p class="mt-4">2. What is your investment horizon?</p>
               <v-radio-group v-model="newProfileForm.invest_goal.investment_horizon">
                 <v-radio label="Short-term (< 1 year)" value="short_term"></v-radio>
                 <v-radio label="Mid-term (1-5 years)" value="mid_term"></v-radio>
                 <v-radio label="Long-term (> 5 years)" value="long_term"></v-radio>
               </v-radio-group>
               <p class="mt-4">3. Expected annual return?</p>
               <v-slider v-model="newProfileForm.invest_goal.expected_annual_return_pct" thumb-label="always" :step="1" min="0" max="100">
                 <template v-slot:append>
                    <v-text-field v-model="newProfileForm.invest_goal.expected_annual_return_pct" density="compact" style="width: 80px" type="number" hide-details single-line suffix="%"></v-text-field>
                 </template>
               </v-slider>
            </v-window-item>

            <!-- BƯỚC 4: Knowledge & Experience -->
            <v-window-item :value="4">
              <p class="text-h6 mb-4">Knowledge & Experience</p>
              <p>1. How would you rate your investment knowledge?</p>
              <v-radio-group v-model="newProfileForm.knowledge_exp.investment_knowledge">
                <v-radio label="Beginner" value="beginner"></v-radio>
                <v-radio label="Intermediate" value="intermediate"></v-radio>
                <v-radio label="Advanced" value="advanced"></v-radio>
                <v-radio label="Expert" value="expert"></v-radio>
              </v-radio-group>
              <p class="mt-4">2. Years of investment experience?</p>
              <v-slider v-model="newProfileForm.knowledge_exp.years_of_experience" thumb-label="always" :step="1" min="0" max="50"></v-slider>
            </v-window-item>

            <!-- BƯỚC 5: Capital & Income -->
            <v-window-item :value="5">
              <p class="text-h6 mb-4">Capital & Income</p>
              <p>1. Initial capital for this profile?</p>
              <v-text-field v-model.number="newProfileForm.capital_income.initial_capital" label="Capital" type="number" prefix="$"></v-text-field>
              <p class="mt-4">2. How dependent are you on this investment for income?</p>
              <v-radio-group v-model="newProfileForm.capital_income.income_dependency">
                <v-radio label="Low" value="low"></v-radio>
                <v-radio label="Medium" value="medium"></v-radio>
                <v-radio label="High" value="high"></v-radio>
              </v-radio-group>
            </v-window-item>
            
            <!-- BƯỚC 6: Preferences & Settings -->
            <v-window-item :value="6">
              <p class="text-h6 mb-4">Preferences & Settings</p>
              <v-combobox
                v-model="newProfileForm.personal_prefer.preferred_sectors"
                label="Preferred Sectors (optional)"
                hint="Type and press Enter to add"
                multiple
                chips
              ></v-combobox>
              <v-combobox
                v-model="newProfileForm.personal_prefer.excluded_sectors"
                label="Excluded Sectors (optional)"
                hint="Type and press Enter to add"
                multiple
                chips
                class="mt-4"
              ></v-combobox>
              <v-switch v-model="newProfileForm.personal_prefer.ethical_investing" color="primary" label="Prioritize Ethical (ESG) Investing"></v-switch>
              <v-divider class="my-4"></v-divider>
              <v-switch v-model="newProfileForm.use_in_advisor" color="primary" label="Use this profile in Advisor for recommendations"></v-switch>
              <v-switch v-model="newProfileForm.is_default" color="primary" label="Set as my default profile"></v-switch>
            </v-window-item>
          </v-window>
        </v-card-text>

        <v-card-actions>
          <v-btn v-if="wizardStep > 1" @click="wizardStep--">Back</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="dialogCreate = false">Cancel</v-btn>
          <v-btn v-if="wizardStep < totalWizardSteps" color="primary" @click="wizardStep++">Next</v-btn>
          <v-btn v-else color="success" @click="handleCreateProfile">Create Profile</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.dialog-scrollable-content {
  max-height: calc(80vh - 150px); /* 80% chiều cao màn hình trừ đi các phần khác */
  overflow-y: auto;
}
</style>
```
- profiles/[profile_id].vue
```vue
<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { storeToRefs } from 'pinia';
import { useProfileStore } from '@/stores/profilesStore';
import type { components } from '@/types/api';

// --- TYPE DEFINITIONS ---
type Profile = components['schemas']['ProfileResponse'];
type ProfileUpdate = components['schemas']['ProfileUpdateRequest'];

// --- STORE & ROUTER ---
const profileStore = useProfileStore();
const { currentProfile, isLoadingDetails, error } = storeToRefs(profileStore);
const route = useRoute('/profiles/[profile_id]');
const router = useRouter();
const profileId = route.params.profile_id as string;

// --- LOCAL STATE ---
// Thay đổi kiểu dữ liệu ở đây: editableProfile sẽ luôn có cấu trúc đầy đủ
const editableProfile = ref<Profile | null>(null);
const isSaving = ref(false);
const isDeleting = ref(false);

// --- LOGIC ---
watch(currentProfile, (newProfileData) => {
  if (newProfileData) {
    // Chỉ cần tạo một bản sao sâu. Kiểu `Profile` đảm bảo tất cả các
    // object con như `risk_tolerance` đều tồn tại.
    editableProfile.value = JSON.parse(JSON.stringify(newProfileData));
  }
}, { immediate: true });


// --- API ACTIONS ---
async function handleUpdateProfile() {
  if (!editableProfile.value) return;
  isSaving.value = true;
  
  // Quan trọng: Trước khi gửi đi, chúng ta tạo một đối tượng ProfileUpdate
  // chỉ chứa những trường thực sự cần thiết.
  // Mặc dù editableProfile có tất cả các trường, nhưng `profile_in`
  // sẽ chỉ chứa những gì `ProfileUpdate` schema định nghĩa.
  const profile_in: ProfileUpdate = {
      profile_name: editableProfile.value.profile_name,
      description: editableProfile.value.description,
      risk_tolerance: editableProfile.value.risk_tolerance,
      invest_goal: editableProfile.value.invest_goal,
      knowledge_exp: editableProfile.value.knowledge_exp,
      capital_income: editableProfile.value.capital_income,
      personal_prefer: editableProfile.value.personal_prefer,
      use_in_advisor: editableProfile.value.use_in_advisor,
      is_default: editableProfile.value.is_default
  };

  const success = await profileStore.updateProfile(profileId, profile_in);
  isSaving.value = false;

  if (success) {
    alert("Profile updated successfully!");
    router.push('/profiles');
  } else {
    alert("Failed to update profile.");
  }
}

async function handleDeleteProfile() {
  if (window.confirm("Are you sure you want to delete this profile? This action cannot be undone.")) {
    isDeleting.value = true;
    const success = await profileStore.deleteProfile(profileId);
    isDeleting.value = false;
    if (success) {
      alert("Profile deleted successfully!");
      router.push('/profiles');
    } else {
      alert("Failed to delete profile.");
    }
  }
}

// --- LIFECYCLE HOOK ---
onMounted(() => {
  profileStore.fetchProfileDetails(profileId);
});
</script>

<template>
  <v-container>
    <!-- Giao diện Loading và Error -->
    <div v-if="isLoadingDetails" class="text-center pa-10">
      <v-progress-circular indeterminate color="primary"></v-progress-circular>
      <p class="mt-4">Loading profile details...</p>
    </div>
    <v-alert v-else-if="error" type="error" class="mb-4" closable>{{ error }}</v-alert>

    <!-- Form chỉnh sửa chính -->
    <v-form v-else-if="editableProfile" @submit.prevent="handleUpdateProfile">
      <!-- Thanh Header với các nút hành động -->
      <div class="d-flex justify-space-between align-center mb-6">
        <div>
          <h1 class="text-h4">Edit Profile</h1>
          <p class="text-subtitle-1">{{ editableProfile.profile_name }}</p>
        </div>
        <div>
          <v-btn to="/profiles" class="mr-2">Cancel</v-btn>
          <v-btn type="submit" color="primary" :loading="isSaving">Save Changes</v-btn>
        </div>
      </div>
      
      <v-row>
        <!-- CỘT BÊN TRÁI -->
        <v-col cols="12" md="6">
          <v-card class="pa-2">
            <v-card-title>Basic Info</v-card-title>
            <v-card-text>
              <v-text-field v-model="editableProfile.profile_name" label="Profile Name"></v-text-field>
              <v-textarea v-model="editableProfile.description" label="Description"></v-textarea>
            </v-card-text>
            
            <v-divider class="my-2"></v-divider>

            <v-card-title>Risk Tolerance</v-card-title>
            <v-card-text>
              <p>Overall risk tolerance?</p>
              <v-radio-group v-model="editableProfile.risk_tolerance.risk_appetite">
                <v-radio label="Very Conservative" value="very_conservative"></v-radio>
                <v-radio label="Conservative" value="conservative"></v-radio>
                <v-radio label="Moderate" value="moderate"></v-radio>
                <v-radio label="Aggressive" value="aggressive"></v-radio>
                <v-radio label="Very Aggressive" value="very_aggressive"></v-radio>
              </v-radio-group>
            </v-card-text>

            <v-divider class="my-2"></v-divider>

            <v-card-title>Knowledge & Experience</v-card-title>
            <v-card-text>
              <p>Investment knowledge?</p>
               <v-radio-group v-model="editableProfile.knowledge_exp.investment_knowledge">
                <v-radio label="Beginner" value="beginner"></v-radio>
                <v-radio label="Intermediate" value="intermediate"></v-radio>
                <v-radio label="Advanced" value="advanced"></v-radio>
                <v-radio label="Expert" value="expert"></v-radio>
              </v-radio-group>
               <p class="mt-2">Years of investment experience?</p>
              <v-slider v-model="editableProfile.knowledge_exp.years_of_experience" thumb-label="always" :step="1" min="0" max="50"></v-slider>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- CỘT BÊN PHẢI -->
        <v-col cols="12" md="6">
          <v-card class="pa-2">
             <v-card-title>Investment Goals</v-card-title>
             <v-card-text>
                <p>Primary investment goal?</p>
               <v-radio-group v-model="editableProfile.invest_goal.primary_goal">
                 <v-radio label="Capital Preservation" value="capital_preservation"></v-radio>
                 <v-radio label="Income Generation" value="income_generation"></v-radio>
                 <v-radio label="Capital Growth" value="capital_growth"></v-radio>
                 <v-radio label="Speculation" value="speculation"></v-radio>
               </v-radio-group>
               <p class="mt-2">Investment horizon?</p>
               <v-radio-group v-model="editableProfile.invest_goal.investment_horizon">
                 <v-radio label="Short-term (< 1 year)" value="short_term"></v-radio>
                 <v-radio label="Mid-term (1-5 years)" value="mid_term"></v-radio>
                 <v-radio label="Long-term (> 5 years)" value="long_term"></v-radio>
               </v-radio-group>
               <p class="mt-2">Expected annual return?</p>
               <v-slider v-model="editableProfile.invest_goal.expected_annual_return_pct" thumb-label="always" :step="1" min="0" max="100" label="%"></v-slider>
             </v-card-text>

            <v-divider class="my-2"></v-divider>

            <v-card-title>Capital & Income</v-card-title>
            <v-card-text>
              <p>Initial capital for this profile?</p>
              <v-text-field v-model.number="editableProfile.capital_income.initial_capital" label="Capital" type="number" prefix="$"></v-text-field>
              <p class="mt-2">Dependency on investment income?</p>
              <v-radio-group v-model="editableProfile.capital_income.income_dependency">
                <v-radio label="Low" value="low"></v-radio>
                <v-radio label="Medium" value="medium"></v-radio>
                <v-radio label="High" value="high"></v-radio>
              </v-radio-group>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
      
      <!-- Card cho Preferences & Settings -->
      <v-card class="mt-6 pa-2">
        <v-card-title>Preferences & Settings</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <v-combobox
                v-model="editableProfile.personal_prefer.preferred_sectors"
                label="Preferred Sectors (optional)"
                hint="Type and press Enter to add"
                multiple
                chips
              ></v-combobox>
            </v-col>
            <v-col cols="12" md="6">
              <v-combobox
                v-model="editableProfile.personal_prefer.excluded_sectors"
                label="Excluded Sectors (optional)"
                hint="Type and press Enter to add"
                multiple
                chips
              ></v-combobox>
            </v-col>
            <v-col cols="12">
               <v-switch v-model="editableProfile.personal_prefer.ethical_investing" color="primary" label="Prioritize Ethical (ESG) Investing"></v-switch>
               <v-switch v-model="editableProfile.use_in_advisor" color="primary" label="Use this profile in Advisor for recommendations"></v-switch>
               <v-switch v-model="editableProfile.is_default" color="primary" label="Set as my default profile"></v-switch>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- VÙNG NGUY HIỂM - XÓA PROFILE -->
      <v-card class="mt-6 pa-2" variant="tonal" color="error">
        <v-card-title>Danger Zone</v-card-title>
        <v-card-text>
          <p>Deleting a profile is a permanent action and cannot be undone.</p>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" variant="flat" @click="handleDeleteProfile" :loading="isDeleting">
            Delete This Profile
          </v-btn>
        </v-card-actions>
      </v-card>

    </v-form>
  </v-container>
</template>
```
- auth/google/callback.vue
```vue
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
```
# Layouts
- default.vue
```vue
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
```
# Components
- TreeNode.vue
```vue
<!-- src/components/TreeNode.vue -->
<script setup lang="ts">
import type { components } from '@/types/api';

type NodeEntity = components['schemas']['NodeEntity'];

// Component này nhận vào một node và độ sâu của nó trong cây
defineProps<{
  node: NodeEntity;
  depth: number;
}>();

// Nó có thể phát ra sự kiện khi một node được click
const emit = defineEmits<{
  (e: 'node-click', nodeName: string): void;
}>();

function onNodeClick(nodeName: string) {
  emit('node-click', nodeName);
}
</script>

<template>
  <div class="tree-node">
    <!-- Hiển thị node hiện tại -->
    <div 
      class="node-content" 
      :style="{ paddingLeft: `${depth * 20}px` }" 
      @click.stop="onNodeClick(node.node_name)"
    >
      <v-icon size="small" class="mr-1">mdi-circle-small</v-icon>
      <v-chip size="small" label class="node-chip">
        {{ node.node_name }}
      </v-chip>
    </div>

    <!-- Nếu có node con, render chúng bằng cách gọi lại chính component này -->
    <div v-if="node.children && node.children.length > 0" class="node-children">
      <TreeNode 
        v-for="(child, index) in node.children" 
        :key="index"
        :node="child"
        :depth="depth + 1"
        @node-click="onNodeClick"
      />
    </div>
  </div>
</template>

<style scoped>
.node-content {
  display: flex;
  align-items: center;
  padding: 4px 0;
  cursor: pointer;
}
.node-chip {
  cursor: pointer;
  transition: background-color 0.2s;
}
.node-chip:hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
}
</style>
```
# Stores
- analysisStore.ts
```typescript
import { defineStore } from "pinia";
import axios from "@/plugins/axios";
import type { components } from "@/types/api";

type AnalysisReport = components['schemas']['QuickCheckReportResponse']

interface State {
  report: AnalysisReport | null;
  explaination: string;
  isLoading: boolean;
  error: string | null;
};

export const useAnalysisStore = defineStore('analysis', {
  state: (): State => ({
    report: null,
    explaination: '',
    isLoading: true,
    error: null
  }), 
  actions: {
    async fetchReport(ticker: string, queryParams: Record<string, any>) {
      this.$reset(); // Reset state trước mỗi lần gọi mới
      this.isLoading = true;
      try {
        const baseUrl = `/api/v1/analysis/quick/${ticker}`;
        const jsonPromise = axios.get(`/analysis/quick/${ticker}/full`, { params: queryParams });
        const textPromise = axios.get(`/analysis/quick/${ticker}/explain`, { params: queryParams });
        const [jsonResponse, textResponse] = await Promise.all([jsonPromise, textPromise]);
        this.report = jsonResponse.data;
        this.explaination = textResponse.data;
      } catch (e: any) {
        this.error = `Could not fetch analysis for ${ticker}. Error: ${e.message}`;
      } finally {
        this.isLoading = false;
      }
    },
  },
});
```
- advisorStore.ts
```typescript
import { defineStore } from 'pinia';
import axios from '@/plugins/axios';
import type { components } from '@/types/api';

type AdvisorReport = components['schemas']['AdvisorResponse'];

interface State {
  report: AdvisorReport | null;
  explaination: string;
  isLoading: boolean;
  error: string | null;
}

export const useAdvisorStore = defineStore('advisor', {
  state: (): State => ({
    report: null,
    explaination: '',
    isLoading: true,
    error: null,
  }),
  actions: {
    async fetchReport(ticker: string, userId: string) {
      this.$reset();
      this.isLoading = true;
      try {
        const apiParams = { user_id: userId };
        const jsonPromise = axios.get(`/advisor/quick/${ticker}/full`, { params: apiParams });
        const textPromise = axios.get(`/advisor/quick/${ticker}/explain`, { params: apiParams });
        const [jsonResponse, textResponse] = await Promise.all([jsonPromise, textPromise]);
        this.report = jsonResponse.data;
        this.explaination = textResponse.data;
      } catch (e: any) {
        this.error = `Could not fetch advisory for ${ticker}. Error: ${e.message}`;
      } finally {
        this.isLoading = false;
      }
    },
  },
});
```
- authStore.ts
```typescript
// src/stores/authStore.ts

import { defineStore } from 'pinia';
import axios from '@/plugins/axios';
import router from '@/router'; // Import trực tiếp router instance
import type { components } from '@/types/api';

type UserInfo = components['schemas']['UserResponse'];

interface AuthState {
  user: UserInfo | null;
  token: string | null;
  isLoading: boolean;
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    token: localStorage.getItem('authToken'),
    isLoading: false,
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    userName: (state) => state.user?.full_name || 'Guest',
  },

  actions: {
    /**
     * Bắt đầu luồng đăng nhập
     */
    async redirectToGoogle() {
      if (this.isLoading) return;
      this.isLoading = true;
      try {
        const response = await axios.get('/auth/google/login');
        window.location.href = response.data.authorization_url;
      } catch (error) {
        console.error("Failed to get Google authorization URL", error);
        this.isLoading = false;
      }
    },

    /**
     * MỚI: Được gọi từ trang callback sau khi đăng nhập thành công
     */
    async handleLoginSuccess(token: string) {
      // 1. Lưu token vào state và localStorage
      this.token = token;
      localStorage.setItem('authToken', token);

      // 2. Gọi API để lấy thông tin người dùng
      await this.fetchCurrentUser();
    },
    
    /**
     * MỚI: Gọi API /users/me để lấy thông tin user
     */
    async fetchCurrentUser() {
      if (!this.token) return;

      try {
        // Cấu hình Axios để gửi token trong header
        const response = await axios.get('/users/me', {
          headers: {
            Authorization: `Bearer ${this.token}`,
          },
        });
        this.user = response.data;
      } catch (error) {
        console.error("Failed to fetch user info. Token might be invalid.", error);
        // Nếu token không hợp lệ, hãy logout
        this.logout();
      }
    },

    /**
     * Đăng xuất
     */
    logout() {
      this.token = null;
      this.user = null;
      localStorage.removeItem('authToken');
      // Dùng router đã import để đảm bảo hoạt động ở mọi nơi
      router.push('/login');
    },

    /**
     * MỚI: Được gọi khi ứng dụng khởi động
     */
    async initializeAuth() {
      if (this.token) {
        console.log("Token found in storage, fetching user info...");
        await this.fetchCurrentUser();
      }
    }
  },
});
```
- notificationStore.ts
```typescript
import { defineStore } from "pinia";

interface State {
  message: string;
  color: string;
  visible: boolean;
  timeout: number;
}

export const useNotificationStore = defineStore('notification', {
  state: (): State => ({
    message: '',
    color: 'info',
    visible: false,
    timeout: 5000, // 5 second
  }),
  actions: {
    showNotification(payload: { message: string, color?: string, timeout?: number }) {
      this.message = payload.message;
      this.color = payload.color || 'info';
      this.timeout = payload.timeout || 5000;
      this.visible = true;
    },
  },
});
```
- profilesStore.ts
```typescript
// src/stores/profileStore.ts
import { defineStore } from 'pinia';
import axios from '@/plugins/axios'; // Import axios đã được cấu hình
import type { components } from '@/types/api';
import { useAuthStore } from './authStore'; // Import authStore

type Profile = components['schemas']['ProfileResponse'];
type ProfileCreate = components['schemas']['ProfileCreateRequest'];
type ProfileUpdate = components['schemas']['ProfileUpdateRequest'];

interface State {
  profiles: Profile[];
  currentProfile: Profile | null;
  isLoadingList: boolean;
  isLoadingDetails: boolean;
  error: string | null;
}

export const useProfileStore = defineStore('profile', {
  state: (): State => ({
    profiles: [],
    currentProfile: null,
    isLoadingList: false,
    isLoadingDetails: false,
    error: null,
  }),
  actions: {
    // Lấy danh sách tất cả profile
    async fetchProfiles() {
      // 1. Kiểm tra xem người dùng đã đăng nhập chưa từ authStore
      const authStore = useAuthStore();
      if (!authStore.isLoggedIn) return; // Không làm gì nếu chưa đăng nhập

      this.isLoadingList = true;
      this.error = null;
      try {
        // 2. Không cần thêm header nữa! Interceptor sẽ tự làm.
        const response = await axios.get('/profiles');
        this.profiles = response.data;
      } catch (e: any) {
        this.error = "Failed to fetch profiles.";
        console.error(e);
      } finally {
        this.isLoadingList = false;
      }
    },

    // Lấy chi tiết một profile
    async fetchProfileDetails(profileId: string) {
      this.isLoadingDetails = true;
      this.currentProfile = null;
      this.error = null;
      try {
        // 3. Không cần thêm header
        const response = await axios.get(`/profiles/${profileId}`);
        this.currentProfile = response.data;
      } catch (e: any) {
        this.error = "Failed to fetch profile details.";
        console.error(e);
      } finally {
        this.isLoadingDetails = false;
      }
    },

    // Tạo profile mới
    async createProfile(profileData: ProfileCreate) {
      try {
        // 4. Không cần thêm header
        const response = await axios.post('/profiles', profileData);
        this.profiles.unshift(response.data);
        return true;
      } catch (e: any) {
        this.error = "Failed to create profile.";
        console.error(e);
        return false;
      }
    },
    
    // --- MỚI: Action để cập nhật profile ---
    async updateProfile(profileId: string, profileData: ProfileUpdate) {
      this.error = null;
      try {
        // Gửi request PUT đến API
        const response = await axios.put(`/profiles/${profileId}`, profileData);
        
        // Cập nhật lại state cục bộ để giao diện thay đổi ngay lập tức
        
        // 1. Cập nhật trong danh sách `profiles`
        const index = this.profiles.findIndex(p => p.profile_id === profileId);
        if (index !== -1) {
          this.profiles[index] = response.data;
        }

        // 2. Cập nhật `currentProfile` nếu nó đang được hiển thị
        if (this.currentProfile?.profile_id === profileId) {
          this.currentProfile = response.data;
        }
        
        return true; // Báo thành công
      } catch (e: any) {
        this.error = "Failed to update profile.";
        console.error(e);
        return false; // Báo thất bại
      }
    },

    // --- MỚI: Action để xóa profile ---
    async deleteProfile(profileId: string) {
      this.error = null;
      try {
        // Gửi request DELETE đến API
        await axios.delete(`/profiles/${profileId}`);

        // Xóa profile khỏi danh sách `profiles` trong state
        this.profiles = this.profiles.filter(p => p.profile_id !== profileId);

        // Nếu profile đang được xem chi tiết bị xóa, hãy xóa nó đi
        if (this.currentProfile?.profile_id === profileId) {
          this.currentProfile = null;
        }
        
        return true; // Báo thành công
      } catch (e: any) {
        this.error = "Failed to delete profile.";
        console.error(e);
        return false; // Báo thất bại
      }
    }
  },
});
```
- rulesStore.ts
```typescript
import { defineStore } from 'pinia';
import axios from '@/plugins/axios';
import type { components } from '@/types/api';

type RuleResponse = components['schemas']['RuleResponse'];
type RuleExplanation = components['schemas']['ExplainationRuleResponse'];
type NodeSpec = components['schemas']['NodeResponse'];
type SemanticType = components['schemas']['SemanticType'];

interface State {
  rulesList: RuleResponse[];
  nodeDictionary: NodeSpec[];
  currentRule: RuleExplanation | null;
  isLoadingList: boolean;
  isLoadingDetails: boolean;
  error: string | null;
}

export const useRulesStore = defineStore('rules', {
  state: (): State => ({
    rulesList: [],
    nodeDictionary: [], // Sẽ được cache ở đây
    currentRule: null,
    isLoadingList: false,
    isLoadingDetails: false,
    error: null,
  }),
  actions: {
    async fetchRules(purpose: SemanticType = 'ANY') {
      this.isLoadingList = true;
      this.error = null;
      try {
        const response = await axios.get('/rules', {
          params: { purpose }
        });
        this.rulesList = response.data;
      } catch (e: any) {
        this.error = `Could not fetch rules. Error: ${e.message}`;
      } finally {
        this.isLoadingList = false;
      }
    },
    
    // Action này chỉ gọi API nếu "từ điển" chưa được tải
    async fetchNodeDictionary() {
      if (this.nodeDictionary.length > 0) return; // Đã có dữ liệu, không cần gọi lại

      try {
        const response = await axios.get('/rules/nodes');
        this.nodeDictionary = response.data;
      } catch (e: any) {
        this.error = `Could not fetch node dictionary. Error: ${e.message}`;
      }
    },
    
    async fetchRuleExplanation(ruleId: string) {
      this.isLoadingDetails = true;
      this.error = null;
      this.currentRule = null;
      try {
        // Luôn đảm bảo "từ điển" node đã được tải
        await this.fetchNodeDictionary();
        
        const response = await axios.get(`/rules/${ruleId}/explain`);
        this.currentRule = response.data;
      } catch (e: any) {
        this.error = `Could not fetch explanation for ${ruleId}. Error: ${e.message}`;
      } finally {
        this.isLoadingDetails = false;
      }
    }
  }
});
```
# Router
- guards.ts
```typescript
import type { Router } from 'vue-router';
import { useAuthStore } from '@/stores/authStore';

const protectedRoutes = ['/profiles']

export function setupNavigationGuards(router: Router) {
    router.beforeEach((to, from, next) => {
        const authStore = useAuthStore();
        const isLoggedIn = authStore.isLoggedIn;

        const requiresAuth = protectedRoutes.includes(to.path);

        //Quy tắc 1: Cố gắng truy cập vào trang được bảo vệ khi đang đăng nhập
        if (requiresAuth && !isLoggedIn) {
            //Điều hướng về trang đăng nhập
            next({ name: '/login' });
        }
        // Quy tắc 2: Cố gắng truy cập trang /login khi đã đăng nhập
        else if (to.path == '/login' && isLoggedIn) {
            //Điều về home page
            next({ name: '/' });
        } 
        // Quy tắc 3: Cho phép đi tiếp
        else {
            next();
        }
    });
}
```
# Plugins
- axios.ts
```typescript
// src/plugins/axios.ts

import axios from 'axios';
import { useAuthStore } from '@/stores/authStore';

// Cấu hình các giá trị mặc định cho axios
axios.defaults.baseURL = import.meta.env.VITE_API_BASE_URL; // Đặt base URL ở đây
axios.defaults.headers.common['Content-Type'] = 'application/json';

// --- Axios Request Interceptor ---
// Đây là "người gác cổng" cho các request gửi đi.
axios.interceptors.request.use(
  (config) => {
    // Khởi tạo authStore để lấy token
    // Lưu ý: Không dùng storeToRefs ở đây
    const authStore = useAuthStore();
    const token = authStore.token; // Lấy token từ state của authStore

    // Nếu có token, đính kèm nó vào header Authorization
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config; // Trả về config đã được sửa đổi
  },
  (error) => {
    // Xử lý lỗi nếu có
    return Promise.reject(error);
  }
);

// (Tùy chọn) Bạn cũng có thể thêm interceptor cho response ở đây
// để xử lý các lỗi chung như 401 Unauthorized
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      // Nếu nhận được lỗi 401 (token không hợp lệ/hết hạn)
      const authStore = useAuthStore();
      authStore.logout(); // Tự động logout người dùng
    }
    return Promise.reject(error);
  }
);

export default axios;
```
