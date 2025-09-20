<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { storeToRefs } from 'pinia';
import { useAdvisorStore } from '@/stores/advisorStore';
import { useProfileStore } from '@/stores/profilesStore';
import { useNotificationStore } from '@/stores/notificationStore';
import ConfigEditor from '@/components/advisor/ConfigEditor.vue';
import FinalActionCard from '@/components/advisor/FinalActionCard.vue';

// --- STORES & STATE ---
const advisorStore = useAdvisorStore();
const profileStore = useProfileStore();
const notificationStore = useNotificationStore();

const { profiles, isLoadingList: isLoadingProfiles } = storeToRefs(profileStore);
const {
  activeProfile,
  editableConfig,
  finalReport,
  isLoadingSuggestion,
  isLoadingReport,
  error
} = storeToRefs(advisorStore);

const route = useRoute('/advisor/[ticker]');
const ticker = route.params.ticker as string;

const selectedProfileId = ref<string | null>(null);
const step = ref(1);

// --- COMPUTED PROPERTIES ---
const currentUIState = computed(() => {
    if (isLoadingSuggestion.value) return 'Loading Suggestion';
    if (!activeProfile.value) return 'Waiting for Profile Selection';
    if (activeProfile.value && editableConfig.value) return 'Ready for Configuration';
    return 'Unknown State';
});

// --- METHODS ---
async function startSuggestionPhase() {
  if (!selectedProfileId.value) return;
  
  const profileObject = profiles.value.find(p => p.profile_id === selectedProfileId.value);
  if (profileObject) {
    await advisorStore.fetchSuggestedConfig(profileObject);
  }
}

async function getFinalAdvice() {
  await advisorStore.fetchFinalReport(ticker);
  
  if (advisorStore.error) {
    notificationStore.showNotification({ 
      message: advisorStore.error, 
      color: 'error' 
    });
  } else {
    step.value = 2;
  }
}

// --- LIFECYCLE HOOKS ---
onMounted(() => {
  advisorStore.resetState();
  profileStore.fetchProfiles();
});

onUnmounted(() => {
  advisorStore.resetState();
});
</script>

<template>
  <v-container>
    <h1 class="text-h4 mb-2">Advisor for: {{ ticker.toUpperCase() }}</h1>
    <v-divider class="mb-6"></v-divider>

    <!-- PROFILE SELECTION STATE -->
    <div v-if="!activeProfile && !isLoadingSuggestion">
      <v-card class="mx-auto pa-4" max-width="600" :loading="isLoadingProfiles">
        <template v-if="!isLoadingProfiles">
          <v-card-title class="text-h5 text-center">Select a Profile</v-card-title>
          <v-card-text>
            <p class="text-center mb-4">Choose an investment profile to get personalized AI-generated suggestions.</p>
            <v-select
              v-model="selectedProfileId"
              label="Choose Profile"
              :items="profiles"
              item-title="profile_name"
              item-value="profile_id"
              variant="outlined"
              class="mb-4"
              hide-details
            ></v-select>
          </v-card-text>
          <v-card-actions>
            <v-btn 
              block 
              color="primary" 
              size="large" 
              @click="startSuggestionPhase" 
              :disabled="!selectedProfileId"
            >
              Begin Advisory
            </v-btn>
          </v-card-actions>
        </template>
      </v-card>
    </div>

    <!-- LOADING SUGGESTION STATE -->
    <div v-else-if="isLoadingSuggestion" class="text-center pa-10">
      <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
      <p class="mt-4 text-h6">AI is analyzing your profile to generate suggestions...</p>
      <p v-if="activeProfile" class="text-medium-emphasis">
        Using profile: {{ activeProfile.profile_name }}
      </p>
    </div>

    <!-- MAIN STEPPER STATE -->
    <div v-else-if="activeProfile && editableConfig">
      <!-- STEPPER HEADER -->
      <v-stepper v-model="step" alt-labels>
        <v-stepper-header>
          <v-stepper-item 
            title="Step 1: Configure & Refine" 
            :value="1" 
            :complete="step > 1"
          ></v-stepper-item>
          <v-divider></v-divider>
          <v-stepper-item 
            title="Step 2: Final Advice" 
            :value="2"
          ></v-stepper-item>
        </v-stepper-header>
      </v-stepper>

      <!-- STEP CONTENT -->
      <v-card class="mt-4">
        <!-- STEP 1: CONFIGURATION -->
        <v-card-text v-if="step === 1">
          <ConfigEditor v-model="editableConfig" />
          <div class="d-flex justify-end pa-4 mt-4">
            <v-btn 
              color="primary" 
              size="large" 
              @click="getFinalAdvice" 
              :loading="isLoadingReport"
            >
              Get Final Advice
            </v-btn>
          </div>
        </v-card-text>

        <!-- STEP 2: FINAL ADVICE -->
        <v-card-text v-else-if="step === 2">
          <!-- Loading Report -->
          <div v-if="isLoadingReport" class="text-center pa-10">
            <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
            <p class="mt-4 text-h6">Generating your personalized report...</p>
          </div>
          
          <!-- Final Report -->
          <div v-else-if="finalReport">
            <FinalActionCard :finalReport="finalReport" />
            <v-btn @click="step = 1" class="mt-4" color="secondary">
              Back to Configuration
            </v-btn>
          </div>
          
          <!-- No Data State -->
          <v-alert v-else type="info">
            Waiting for report data or an error occurred.
          </v-alert>
        </v-card-text>
      </v-card>
    </div>
    
    <!-- ERROR STATE -->
    <v-alert v-if="error" type="error" class="mt-6" closable>
      {{ error }}
    </v-alert>
  </v-container>
</template>