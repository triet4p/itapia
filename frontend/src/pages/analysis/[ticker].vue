<script lang="ts" setup>
  import { ref, onMounted, computed } from 'vue';
  import { useRoute } from 'vue-router';
  import axios from 'axios';
  import type { components } from '@/types/api';

  // --- TYPE DEFINITIONS ---
  type AnalysisReport = components['schemas']['QuickCheckAnalysisReport'];

  // --- REACTIVE STATE ---
  const analysisData = ref<AnalysisReport | null>(null);
  const explanationText = ref<string>(''); // Biến mới để lưu giải thích text
  const isLoading = ref<boolean>(true);
  const error = ref<string | null>(null);
  const showFullJson = ref<boolean>(false); // Biến mới để điều khiển hiển thị JSON

  // --- ROUTE & PARAMS ---
  const route = useRoute('/analysis/[ticker]'); // Gọi không có tham số
  const ticker = route.params.ticker;

  // Lấy các query params từ URL, cung cấp giá trị mặc định nếu không có
  const queryParams = {
    daily_analysis_type: route.query.daily_analysis_type || 'medium',
    required_type: route.query.required_type || 'all'
  };

  // --- DATA FETCHING ---
  async function fetchAllData() {
    if (!ticker) {
      error.value = "Không tìm thấy mã cổ phiếu.";
      isLoading.value = false;
      return;
    }

    try {
      isLoading.value = true;
      const baseUrl = `http://localhost:8000/api/v1/analysis/quick/${ticker}`;

      // Tạo hai lời hứa (promise) cho hai lời gọi API
      const jsonPromise = axios.get(`${baseUrl}/full`, { params: queryParams });
      const textPromise = axios.get(`${baseUrl}/explain`, { params: queryParams });

      // Sử dụng Promise.all để thực thi cả hai lời gọi song song
      const [jsonResponse, textResponse] = await Promise.all([jsonPromise, textPromise]);

      // Gán kết quả vào các biến reactive tương ứng
      analysisData.value = jsonResponse.data;
      explanationText.value = textResponse.data;

    } catch (e: any) {
      error.value = `Không thể lấy báo cáo cho mã ${ticker}. Lỗi: ${e.message}`;
      console.error(e);
    } finally {
      isLoading.value = false;
    }
  }

  // --- LIFECYCLE HOOK ---
  onMounted(() => {
    fetchAllData();
  });

  // --- COMPUTED PROPERTIES --- (Rất hữu ích để lấy dữ liệu lồng nhau)
  const keyIndicators = computed(() => analysisData.value?.technical_report.daily_report?.key_indicators);
  const trendStrength = computed(() => analysisData.value?.technical_report.daily_report?.trend_report.overall_strength);
  const patterns = computed(() => analysisData.value?.technical_report.daily_report?.pattern_report.top_patterns.slice(0, 3));
</script>

<template>
  <v-container>
    <!-- Giao diện Loading và Error không đổi -->
    <div v-if="isLoading" class="text-center pa-10">
      <v-progress-circular indeterminate color="primary" :size="70" :width="7"></v-progress-circular>
      <h2 class="mt-4">Analyzing {{ ticker }}...</h2>
    </div>
    <v-alert type="error" v-else-if="error" title="Lỗi Phân tích" :text="error" variant="tonal"></v-alert>

    <!-- Giao diện hiển thị dữ liệu đã được cấu trúc lại -->
    <div v-else-if="analysisData">
      <h1 class="text-h4 mb-2">Analysis Report of ticker: {{ analysisData.ticker }}</h1>
      <p class="text-subtitle-1 mb-6">Generated-at {{ new Date(analysisData.generated_at_utc).toLocaleString('vi-VN') }}</p>

      <v-row>
        <!-- CỘT BÊN TRÁI: CÁC CHỈ SỐ CHÍNH & GIẢI THÍCH -->
        <v-col cols="12" md="8">
          <v-card class="mb-6">
            <v-card-title>Explain Summary</v-card-title>
            <v-card-text>
              <pre class="explanation-text">{{ explanationText }}</pre>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- CỘT BÊN PHẢI: KEY INDICATORS -->
        <v-col cols="12" md="4">
          <v-card>
            <v-card-title>Key Indicators</v-card-title>
            <v-list v-if="keyIndicators && trendStrength">
              <v-list-item v-if="keyIndicators.rsi_14" title="RSI (14)" :subtitle="keyIndicators.rsi_14.toFixed(2)"></v-list-item>
              <v-divider></v-divider>
              <v-list-item v-if="trendStrength.strength" title="Trend Strength" :subtitle="`${trendStrength.strength} (${trendStrength.value.toFixed(2)})`"></v-list-item>
              <v-divider></v-divider>
              <v-list-item v-if="keyIndicators.sma_20" title="SMA 20" :subtitle="keyIndicators.sma_20.toFixed(2)"></v-list-item>
              <v-divider></v-divider>
              <v-list-item v-if="keyIndicators.sma_50" title="SMA 50" :subtitle="keyIndicators.sma_50.toFixed(2)"></v-list-item>
              <v-divider></v-divider>
              <v-list-item v-if="patterns" title="Some of patterns">
                <v-list v-for="pattern in patterns">
                  <v-list-item :title="pattern.name + ' (' + pattern.pattern_type + ')'" :subtitle="pattern.sentiment"></v-list-item>
                </v-list>
              </v-list-item>
            </v-list>
          </v-card>
        </v-col>
      </v-row>
      
      <!-- KHU VỰC JSON ĐẦY ĐỦ (CÓ THỂ BẬT/TẮT) -->
      <v-card>
        <v-card-actions>
          <v-btn @click="showFullJson = !showFullJson">
            {{ showFullJson ? 'Hide' : 'Show' }} Full JSON Report
          </v-btn>
        </v-card-actions>
        <v-expand-transition>
          <div v-show="showFullJson">
            <v-divider></v-divider>
            <v-card-text>
              <pre class="json-dump"><code>{{ JSON.stringify(analysisData, null, 2) }}</code></pre>
            </v-card-text>
          </div>
        </v-expand-transition>
      </v-card>
    </div>
  </v-container>
</template>

<style scoped>
.explanation-text, .json-dump {
 background-color: #2d2d2d;
 padding: 16px;
 border-radius: 4px;
 white-space: pre-wrap;
 word-break: break-all;
 font-family: 'Courier New', Courier, monospace;
}
.json-dump {
 background-color: #2d2d2d;
 color: #f8f8f2;
}
</style>