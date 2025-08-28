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
type RuleStatus = components['schemas']['RuleStatus']

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
    title: 'Status', 
    key: 'rule_status', 
    cellProps: { class: 'status-col' },
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
        <template v-slot:item.rule_status="{ value }">
          <v-chip :color="value ? 'success' : 'grey'" size="small">
            {{ value ? 'READY' : 'DEPRECATED' }}
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

:deep(.status-col) {
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