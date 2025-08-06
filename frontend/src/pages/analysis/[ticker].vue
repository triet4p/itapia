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