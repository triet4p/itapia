<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
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
  rulesStore.fetchRuleExplanation(ruleId);
});

//Compute
const performanceMetrics = computed(() => {
  return currentRule.value?.metrics || null;
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
              <v-list-item title="Status">
                <template v-slot:subtitle>
                  <v-chip :color="currentRule.rule_status ? 'success' : 'grey'" size="small">
                    {{ currentRule.rule_status ? 'READY' : 'DEPRECATED' }}
                  </v-chip>
                </template>
              </v-list-item>
              <v-list-item title="Created At" :subtitle="new Date(currentRule.created_at_ts * 1000).toLocaleString('en-GB')"></v-list-item>
            </v-list>
          </v-card>

          <VCard v-if="performanceMetrics">
            <VCardTitle>Peformance metrics</VCardTitle>
            <v-list density="compact">
              <v-list-item title="Total Return" :subtitle="`${(performanceMetrics.total_return_pct * 100).toFixed(2)}%`"></v-list-item>
              <v-list-item title="Win Rate" :subtitle="`${(performanceMetrics.win_rate_pct * 100).toFixed(2)}%`"></v-list-item>
              <v-list-item title="Profit Factor" :subtitle="performanceMetrics.profit_factor.toFixed(2)"></v-list-item>
              <v-list-item title="Max Drawdown" :subtitle="`${(performanceMetrics.max_drawdown_pct * 100).toFixed(2)}%`"></v-list-item>
              <v-list-item title="Sharpe Ratio" :subtitle="performanceMetrics.sharpe_ratio.toFixed(2)"></v-list-item>
              <v-list-item title="Number of Trades" :subtitle="performanceMetrics.num_trades"></v-list-item>
              <v-list-item title="Sortino Ratio" :subtitle="performanceMetrics.sortino_ratio.toFixed(2)"></v-list-item>
              <v-list-item title="Annual Return Stability" :subtitle="performanceMetrics.annual_return_stability.toFixed(2)"></v-list-item>
              <v-list-item title="CAGR" :subtitle="performanceMetrics.cagr.toFixed(2)"></v-list-item>
            </v-list>
          </VCard>
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