<script setup lang="ts">
import { computed } from 'vue';
import type { components } from '@/types/api';

type AdvisorReport = components['schemas']['AdvisorResponse'];
type FinalRecommendation = components['schemas']['FinalRecommendation'];

// State cục bộ để điều khiển việc hiển thị JSON
const showFullJson = ref(false);

const props = defineProps<{
  finalReport: AdvisorReport;
}>();

// Helper để lấy ra thông tin hiển thị chính
const actionDetails = computed(() => {
  const actionType = props.finalReport.final_action.action_type;
  switch (actionType) {
    case 'BUY':
      return { text: 'BUY', color: 'success', icon: 'mdi-arrow-up-bold-circle' };
    case 'SELL':
      return { text: 'SELL', color: 'error', icon: 'mdi-arrow-down-bold-circle' };
    case 'HOLD':
      return { text: 'HOLD', color: 'grey-darken-1', icon: 'mdi-pause-circle' };
    default:
      return { text: 'UNKNOWN', color: 'grey', icon: 'mdi-help-circle' };
  }
});

// Helper để lấy màu cho các chip khuyến nghị
function getChipColor(label: string): string {
  const upperLabel = label.toUpperCase();
  if (upperLabel.includes('BUY') || upperLabel.includes('POSITIVE') || upperLabel.includes('STRONG') || upperLabel.includes('INTERESTING') || upperLabel.includes('ACCUMULATE')) return 'success';
  if (upperLabel.includes('SELL') || upperLabel.includes('NEGATIVE') || upperLabel.includes('RISK_HIGH') || upperLabel.includes('AVOID') || upperLabel.includes('REDUCE')) return 'error';
  return 'grey';
}

// Helper để làm sạch văn bản khuyến nghị
function cleanRecommendText(recommend: string, purpose: string): string {
    return recommend.replace(`Threshold match is THRESHOLD_${purpose}_`, "").replace(", which mean ", ": ");
}
</script>

<template>
  <v-card>
    <v-card-item class="pb-0">
      <template v-slot:prepend>
        <v-icon :color="actionDetails.color" :icon="actionDetails.icon" size="x-large"></v-icon>
      </template>
      <v-card-title class="text-h5">{{ actionDetails.text }}</v-card-title>
      <v-card-subtitle>Final Action Recommendation</v-card-subtitle>
    </v-card-item>

    <v-card-text>
      <v-list>
        <v-list-item
          prepend-icon="mdi-chart-pie"
          title="Position Size"
          :subtitle="`${(finalReport.final_action.position_size_pct * 100).toFixed(0)}% of profile capital`"
        ></v-list-item>
        <v-list-item
          prepend-icon="mdi-arrow-up-right"
          title="Take Profit"
          :subtitle="`~${finalReport.final_action.tp_pct.toFixed(2)}%`"
        ></v-list-item>
        <v-list-item
          prepend-icon="mdi-arrow-down-left"
          title="Stop Loss"
          :subtitle="`~${finalReport.final_action.sl_pct.toFixed(2)}%`"
        ></v-list-item>
      </v-list>
    </v-card-text>
    
    <v-divider></v-divider>

    <v-card-text>
      <p class="text-subtitle-1 mb-2">Based on the following signals:</p>
    </v-card-text>
  </v-card>

  <!-- BA CARD PHỤ CHO DECISION, RISK, OPPORTUNITY -->
    <v-row>
      <!-- Card cho Quyết định -->
      <v-col cols="12">
        <v-card>
          <v-list-item prepend-icon="mdi-lightbulb-on-outline" title="Decision Signals" :subtitle="`Final Score: ${finalReport.final_decision.final_score.toFixed(2)}`"></v-list-item>
          <v-card-text>
            <v-chip :color="getChipColor(finalReport.final_decision.label)" class="wrap-chip-text">
              {{ cleanRecommendText(finalReport.final_decision.final_recommend, 'DECISION') }}
            </v-chip>
          </v-card-text>
          <v-expansion-panels variant="accordion">
            <v-expansion-panel title="Triggered Rules">
              <v-expansion-panel-text>
                <v-list density="compact">
                  <v-list-item
                    v-for="rule in finalReport.final_decision.triggered_rules"
                    :key="rule.rule_id"
                    :title="rule.name"
                  >
                    <div>
                      <div class="text-caption text-grey-darken-1">{{ rule.rule_id }}</div>
                      <div class="font-weight-medium">Score: {{ rule.score.toFixed(2) }}</div>
                    </div>
                  </v-list-item>
                </v-list>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card>
      </v-col>

      <!-- Card cho Rủi ro -->
      <v-col cols="12" sm="6">
        <v-card>
            <v-list-item prepend-icon="mdi-lightbulb-on-outline" title="Risk Level" :subtitle="`Final Score: ${finalReport.final_risk.final_score.toFixed(2)}`"></v-list-item>
          <v-card-text>
            <v-chip :color="getChipColor(finalReport.final_risk.label)" class="wrap-chip-text">
              {{ cleanRecommendText(finalReport.final_risk.final_recommend, 'RISK') }}
            </v-chip>
          </v-card-text>
          <v-expansion-panels variant="accordion">
            <v-expansion-panel title="Triggered Rules">
              <v-expansion-panel-text>
                <v-list density="compact">
                  <v-list-item
                    v-for="rule in finalReport.final_risk.triggered_rules"
                    :key="rule.rule_id"
                    :title="rule.name"
                  >
                    <div>
                      <div class="text-caption text-grey-darken-1">{{ rule.rule_id }}</div>
                      <div class="font-weight-medium">Score: {{ rule.score.toFixed(2) }}</div>
                    </div>
                  </v-list-item>
                </v-list>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card>
      </v-col>

      <!-- Card cho Cơ hội -->
      <v-col cols="12" sm="6">
        <v-card>
            <v-list-item prepend-icon="mdi-lightbulb-on-outline" title="Opportunity Rating" :subtitle="`Final Score: ${finalReport.final_opportunity.final_score.toFixed(2)}`"></v-list-item>
          <v-card-text>
            <v-chip :color="getChipColor(finalReport.final_opportunity.label)" class="wrap-chip-text">
              {{ cleanRecommendText(finalReport.final_opportunity.final_recommend, 'OPPORTUNITY') }}
            </v-chip>
          </v-card-text>
          <v-expansion-panels variant="accordion">
            <v-expansion-panel title="Triggered Rules">
              <v-expansion-panel-text>
                <v-list density="compact">
                  <v-list-item
                    v-for="rule in finalReport.final_opportunity.triggered_rules"
                    :key="rule.rule_id"
                    :title="rule.name"
                  >
                    <div>
                      <div class="text-caption text-grey-darken-1">{{ rule.rule_id }}</div>
                      <div class="font-weight-medium">Score: {{ rule.score.toFixed(2) }}</div>
                    </div>
                  </v-list-item>
                </v-list>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card>
      </v-col>
    </v-row>

    <!-- CARD HIỂN THỊ JSON -->
    <v-card class="mt-6">
      <v-card-actions>
        <v-btn @click="showFullJson = !showFullJson">
          {{ showFullJson ? 'Hide' : 'Show' }} Full JSON Report
        </v-btn>
      </v-card-actions>
      <v-expand-transition>
        <div v-show="showFullJson">
          <v-divider></v-divider>
          <v-card-text>
            <pre class="json-dump"><code>{{ JSON.stringify(finalReport, null, 2) }}</code></pre>
          </v-card-text>
        </div>
      </v-expand-transition>
    </v-card>
</template>

<style scoped>
.wrap-chip-text {
  height: auto !important;
  white-space: normal;
  padding: 4px 8px;
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
</style>