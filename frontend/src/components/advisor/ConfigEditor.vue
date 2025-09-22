<!--
  Configuration Editor Component
  
  Allows users to customize quantitative preferences for the investment advisor.
  Includes controls for adjusting weights, constraints, and behavior modifiers.
-->
<script setup lang="ts">
import { computed } from 'vue';
import type { components } from '@/types/api';

// --- TYPE DEFINITIONS ---
type QuantitativeConfig = components['schemas']['QuantitivePreferencesConfigRequest'];
type Weights = components['schemas']['PerformanceFilterWeights'];
type Constraints = components['schemas']['PerformanceHardConstraints'];
type ConstraintKeys = keyof Constraints;

// --- PROPS & EMITS ---
/**
 * Props for the Configuration Editor component
 * 
 * @prop modelValue - The quantitative configuration to edit (supports v-model)
 */
const props = defineProps<{
  // Use `modelValue` to enable v-model usage from parent component
  modelValue: QuantitativeConfig;
}>();

/**
 * Emits events from the Configuration Editor component
 * 
 * @event update:modelValue - Emitted when the configuration is updated
 */
const emit = defineEmits<{
  (e: 'update:modelValue', value: QuantitativeConfig): void;
}>();

// --- COMPUTED PROPERTIES ---
// Create computed properties with get/set to work with v-model
// This prevents direct prop mutation and safely emits events
const editableWeights = computed<Weights>({
  get: () => props.modelValue.weights,
  set: (newWeights) => {
    emit('update:modelValue', { ...props.modelValue, weights: newWeights });
  }
});

const editableConstraints = computed<Constraints>({
  get: () => props.modelValue.constraints,
  set: (newConstraints) => {
    emit('update:modelValue', { ...props.modelValue, constraints: newConstraints });
  }
});

/**
 * Metadata for constraint configuration options
 * Contains display information and descriptions for each constraint
 */
const constraintMetadata: { key: ConstraintKeys, title: string, description: string }[] = [
  { 
    key: 'total_return_pct', 
    title: 'Total Return (%)', 
    description: 'The overall profit or loss of the strategy. From 0 (0%) to 1 (100%), often less than 10%'
  },
  { 
    key: 'win_rate_pct', 
    title: 'Win Rate (%)', 
    description: 'From 0 (0%) to 1 (100%)'
  },
  { 
    key: 'max_drawdown_pct', 
    title: 'Max Drawdown (%)', 
    description: 'Often less than 30% (0.3)'
  },
  { 
    key: 'sortino_ratio', 
    title: 'Sortino Ratio', 
    description: 'A variation of the Sharpe ratio that only factors in downside volatility. Often from -5 to 15.'
  },
  {
    key: 'sharpe_ratio',
    title: 'Sharpe Ratio',
    description: 'Often from -3 to 10'
  },
  {
    key: 'annual_return_stability',
    title: 'Annual Return Stability',
    description: 'From 0 to 1, often greater than 0.7',
  },
  {
    key: 'cagr',
    title: 'CAGR',
    description: 'Often small, like from 0.01 to 0.1'
  },
  {
    key: 'profit_factor',
    title: 'Profit Factor',
    description: 'Often from -2 to 5',
  },
  {
    key: 'num_trades',
    title: 'Num of trades',
    description: 'Number of trades generated in past. An non-negative integer'
  }
  // Additional constraints can be easily added here
];
</script>

<template>
  <v-card flat>
    <v-card-text>
      <!-- SECTION 1: WEIGHTS -->
      <p class="text-h6 mb-2">Fitness Weights</p>
      <p class="text-body-2 mb-4">
        Adjust the importance of each metric (from 0 to 1). Higher values mean greater importance.
      </p>

      <v-row>
        <v-col cols="12" md="6"><label>Total Return Percentage</label><v-slider v-model="editableWeights.total_return_pct" thumb-label="always" :step="0.05" min="0" max="1"></v-slider></v-col>
        <v-col cols="12" md="6"><label>Win Rate</label><v-slider v-model="editableWeights.win_rate_pct" thumb-label="always" :step="0.05" min="0" max="1"></v-slider></v-col>
        <v-col cols="12" md="6"><label>Max Drawdown Percentage</label><v-slider v-model="editableWeights.max_drawdown_pct" thumb-label="always" :step="0.05" min="0" max="1"></v-slider></v-col>
        <v-col cols="12" md="6"><label>Sortino Ratio</label><v-slider v-model="editableWeights.sortino_ratio" thumb-label="always" :step="0.05" min="0" max="1"></v-slider></v-col>
        <v-col cols="12" md="6"><label>Sharpe Ratio</label><v-slider v-model="editableWeights.sharpe_ratio" thumb-label="always" :step="0.05" min="0" max="1"></v-slider></v-col>
        <v-col cols="12" md="6"><label>Profit Factor</label><v-slider v-model="editableWeights.profit_factor" thumb-label="always" :step="0.05" min="0" max="1"></v-slider></v-col>
        <v-col cols="12" md="6"><label>CAGR</label><v-slider v-model="editableWeights.cagr" thumb-label="always" :step="0.05" min="0" max="1"></v-slider></v-col>
        <v-col cols="12" md="6"><label>Number of Trades</label><v-slider v-model="editableWeights.num_trades" thumb-label="always" :step="0.05" min="0" max="1"></v-slider></v-col>
        <v-col cols="12" md="6"><label>Annual Return Stability</label><v-slider v-model="editableWeights.annual_return_stability" thumb-label="always" :step="0.05" min="0" max="1"></v-slider></v-col>
      </v-row>

      <v-divider class="my-6"></v-divider>

      <!-- SECTION 2: CONSTRAINTS -->
      <p class="text-h6 mb-2">Hard Constraints</p>
      <p class="text-body-2 mb-4">
        Set the minimum and maximum acceptable values. Leave blank for no limit.
      </p>
      
      <!-- Begin loop -->
      <div v-for="constraint in constraintMetadata" :key="constraint.key" class="constraint-row">
        <v-row align="center" no-gutters>
          <!-- Name and Description Column -->
          <v-col cols="12" md="6" class="pr-4">
            <p class="font-weight-medium">{{ constraint.title }}</p>
            <p class="text-caption text-medium-emphasis">{{ constraint.description }}</p>
          </v-col>

          <!-- Min Input Column -->
          <v-col cols="6" md="3">
            <v-text-field
              v-model.number="modelValue.constraints[constraint.key][0]"
              label="Min"
              type="number"
              variant="outlined"
              density="compact"
              hide-details
              clearable
            ></v-text-field>
          </v-col>

          <!-- Max Input Column -->
          <v-col cols="6" md="3">
            <v-text-field
              v-model.number="modelValue.constraints[constraint.key][1]"
              label="Max"
              type="number"
              variant="outlined"
              density="compact"
              hide-details
              clearable
            ></v-text-field>
          </v-col>
        </v-row>
        <v-divider class="my-4"></v-divider>
      </div>

      <v-divider class="my-6"></v-divider>

      <!-- =============================================== -->
      <!-- SECTION 3: BEHAVIOR MODIFIERS                  -->
      <!-- =============================================== -->
      <p class="text-h6 mb-2">Behavior Modifiers</p>
      <p class="text-body-2 mb-4">Fine-tune the final trading action.</p>
      <v-row>
        <v-col cols="12" md="6">
          <label>Position Sizing Factor (e.g., 1.0 = 100%)</label>
          <v-slider v-model="modelValue.modifiers.position_sizing_factor" thumb-label="always" :step="0.1" min="0.1" max="2"></v-slider>
        </v-col>
        <v-col cols="12" md="6">
          <label>Risk Tolerance Factor (e.g., 1.2 = 20% wider SL/TP)</label>
          <v-slider v-model="modelValue.modifiers.risk_tolerance_factor" thumb-label="always" :step="0.1" min="0.5" max="1.5"></v-slider>
        </v-col>
      </v-row>

    </v-card-text>
  </v-card>
</template>