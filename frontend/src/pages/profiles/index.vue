<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { useProfileStore } from '@/stores/profilesStore';
import type { components } from '@/types/api';
import { useNotificationStore } from '@/stores/notificationStore';

// --- TYPE DEFINITIONS ---
type ProfileCreate = components['schemas']['ProfileCreateRequest'];
type Profile = components['schemas']['ProfileResponse'];

// --- STORE & STATE ---
const profileStore = useProfileStore();
const { profiles, isLoadingList, error } = storeToRefs(profileStore);

const notificationStore = useNotificationStore();

const dialogCreate = ref(false);
const wizardStep = ref(1);
const totalWizardSteps = 6; // Total step to manage create profile

// --- FORM STATE ---
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
  } else {
    notificationStore.showNotification({
      message: 'Creation failed! Please check the console for details.',
      color: 'error',
    })
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

    <!-- DIALOG CREATION GUI BY WIZARD -->
    <v-dialog v-model="dialogCreate" persistent max-width="800px">
      <v-card>
        <v-card-title>
          <span class="text-h5">Create New Profile (Step {{ wizardStep }}/{{ totalWizardSteps }})</span>
        </v-card-title>
        
        <v-card-text class="dialog-scrollable-content">
          <v-window v-model="wizardStep">
            <!-- Step 1: Basic Info -->
            <v-window-item :value="1">
              <p class="text-h6 mb-4">Basic Info</p>
              <v-text-field v-model="newProfileForm.profile_name" label="Profile Name" hint="e.g., Long-term Growth, Safe Retirement" persistent-hint></v-text-field>
              <v-textarea v-model="newProfileForm.description" label="Description" hint="Describe the strategy for this profile" persistent-hint class="mt-4"></v-textarea>
            </v-window-item>
            
            <!-- Step 2: Risk Tolerance -->
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
            
            <!-- Step 3: Investment Goals -->
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

            <!-- Step 4: Knowledge & Experience -->
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

            <!-- Step 5: Capital & Income -->
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
            
            <!-- Step 6: Preferences & Settings -->
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
  max-height: calc(80vh - 150px); 
  overflow-y: auto;
}
</style>