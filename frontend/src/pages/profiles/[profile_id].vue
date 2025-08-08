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