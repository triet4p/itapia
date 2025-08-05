<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import type { components } from '@/types/api';

// --- TYPE DEFINITIONS ---
type AdvisorReport = components['schemas']['AdvisorReportSchema'];
type FinalAdvice = components['schemas']['AdvisorReportSchema'];

// --- REACTIVE STATE ---
const advisorData = ref<AdvisorReport | null>(null);
const explanationText = ref<string>('');
const isLoading = ref<boolean>(true);
const error = ref<string | null>(null);
const showFullJson = ref<boolean>(false);

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

// --- DATA FETCHING ---
async function fetchAdvisoryData() {
  if (!ticker) {
    error.value = "Ticker symbol not found in URL.";
    isLoading.value = false;
    return;
  }
  
  try {
    isLoading.value = true;
    const baseUrl = `http://localhost:8000/api/v1/advisor/quick/${ticker}`;
    const apiParams = {
      user_id: userId.value // Truyền user_id vào params
    };

    const jsonPromise = axios.get(`${baseUrl}/full`, { params: apiParams });
    const textPromise = axios.get(`${baseUrl}/explain`, { params: apiParams });

    const [jsonResponse, textResponse] = await Promise.all([jsonPromise, textPromise]);

    advisorData.value = jsonResponse.data;
    explanationText.value = textResponse.data;

  } catch (e: any) {
    error.value = `Could not fetch advisory for ticker ${ticker}. Error: ${e.message}`;
    console.error(e);
  } finally {
    isLoading.value = false;
  }
}

// --- LIFECYCLE HOOK ---
onMounted(() => {
  fetchAdvisoryData();
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
    <div v-else-if="advisorData">
      <h1 class="text-h4 mb-2">Advisory Report: {{ advisorData.ticker }}</h1>
      <p class="text-subtitle-1 mb-6">Generated at {{ new Date(advisorData.generated_at_utc).toLocaleString('en-GB') }}</p>

      <v-row>
        <!-- CỘT BÊN TRÁI: GIẢI THÍCH CHI TIẾT -->
        <v-col cols="12" md="7">
          <v-card class="mb-6">
            <v-card-title>Explanation Summary</v-card-title>
            <v-card-text>
              <pre class="explanation-text">{{ explanationText }}</pre>
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
              <v-list-item-subtitle>Final Score: {{ advisorData.final_decision.final_score.toFixed(2) }}</v-list-item-subtitle>
            </v-list-item>
            <v-card-text>
              <v-chip :color="getLabelColor(advisorData.final_decision.label)" class="wrap-chip-text">
                {{ advisorData.final_decision.final_recommend.replace("Threshold match is THRESHOLD_DECISION_", "").replace(", which mean ", ": ") }}
              </v-chip>
            </v-card-text>
            <v-expansion-panels variant="accordion">
              <v-expansion-panel title="Triggered Rules">
                <v-expansion-panel-text>
                  <v-list density="compact">
                    <v-list-item
                      v-for="rule in advisorData.final_decision.triggered_rules"
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
              <v-list-item-subtitle>Final Score: {{ advisorData.final_risk.final_score.toFixed(2) }}</v-list-item-subtitle>
            </v-list-item>
            <v-card-text>
              <v-chip :color="getLabelColor(advisorData.final_risk.label)" class="wrap-chip-text">
                {{ advisorData.final_risk.final_recommend.replace("Threshold match is THRESHOLD_RISK_", "").replace(", which mean ", ": ") }}
              </v-chip>
            </v-card-text>
            <v-expansion-panels variant="accordion">
              <v-expansion-panel title="Triggered Rules">
                <v-expansion-panel-text>
                  <v-list density="compact">
                    <v-list-item
                      v-for="rule in advisorData.final_risk.triggered_rules"
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
              <v-list-item-subtitle>Final Score: {{ advisorData.final_opportunity.final_score.toFixed(2) }}</v-list-item-subtitle>
            </v-list-item>
            <v-card-text>
              <v-chip :color="getLabelColor(advisorData.final_opportunity.label)" class="wrap-chip-text">
                {{ advisorData.final_opportunity.final_recommend.replace("Threshold match is THRESHOLD_OPP_RATING_", "").replace(", which mean ", ": ") }}
              </v-chip>
            </v-card-text>
            <v-expansion-panels variant="accordion">
              <v-expansion-panel title="Triggered Rules">
                <v-expansion-panel-text>
                  <v-list density="compact">
                    <v-list-item
                      v-for="rule in advisorData.final_opportunity.triggered_rules"
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
              <pre class="json-dump"><code>{{ JSON.stringify(advisorData, null, 2) }}</code></pre>
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