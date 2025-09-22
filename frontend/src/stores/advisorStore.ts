// src/stores/advisorStore.ts
/**
 * Advisor Store
 * 
 * Manages state and logic for the investment advisor functionality.
 * Handles AI-generated investment recommendations and user configuration.
 */

import { defineStore } from 'pinia';
import axios from 'axios';
import type { components } from '@/types/api';

// --- TYPE DEFINITIONS ---
// Using schemas synchronized from the backend
type Profile = components['schemas']['ProfileResponse'];
type QuantitativeConfig = components['schemas']['QuantitivePreferencesConfigResponse'];
type AdvisorReport = components['schemas']['AdvisorResponse'];
type Constraints = components['schemas']['PerformanceHardConstraints'];

// Define the structure of the State
interface State {
  activeProfile: Profile | null; // Profile currently being used for consultation
  suggestedConfig: QuantitativeConfig | null; // Original configuration suggested by AI
  editableConfig: QuantitativeConfig | null; // Configuration currently being edited by user
  finalReport: AdvisorReport | null; // Final report
  
  // Manage detailed UI state
  isLoadingSuggestion: boolean;
  isLoadingReport: boolean;
  error: string | null;
}

// --- HELPER FUNCTION (Modularization) ---
/**
 * Takes a constraints object and converts empty string values ("")
 * in tuples to null for API submission.
 * 
 * @param originalConstraints - Original constraints object from state
 * @returns A new, cleaned constraints object
 */
function cleanConstraintsForAPI(originalConstraints: Constraints): Constraints {
  // Create a deep copy to avoid modifying the original object
  const cleaned = JSON.parse(JSON.stringify(originalConstraints));

  for (const key in cleaned) {
    const constraintKey = key as keyof Constraints;
    const value = cleaned[constraintKey];

    if (Array.isArray(value)) {
      // Convert "" to null for both min (index 0) and max (index 1)
      value[0] = value[0] === '' ? null : value[0];
      value[1] = value[1] === '' ? null : value[1];
    }
  }
  return cleaned;
}

export const useAdvisorStore = defineStore("advisor", {
  // 1. STATE: Initial state
  state: (): State => ({
    activeProfile: null,
    suggestedConfig: null,
    editableConfig: null,
    finalReport: null,
    isLoadingSuggestion: false,
    isLoadingReport: false,
    error: null,
  }),

  // 2. ACTIONS: Contains business logic
  actions: {
    /**
     * STEP 1: Fetch quantitative configuration suggested by AI.
     * Called when user selects a profile and starts a consultation session.
     */
    async fetchSuggestedConfig(profile: Profile) {
      this.resetState(); // Clean up previous session before starting
      this.isLoadingSuggestion = true;
      this.error = null;
      this.activeProfile = profile;

      try {
        const response = await axios.post('/personal/suggested_config', profile);
        
        // Save result to both states
        const config: QuantitativeConfig = response.data;

        this.suggestedConfig = config;
        // Create a deep copy for user editing
        this.editableConfig = JSON.parse(JSON.stringify(config));

      } catch (e: any) {
        this.error = e.response?.data?.detail || "Failed to generate AI suggestions.";
        console.error(e);
      } finally {
        this.isLoadingSuggestion = false;
      }
    },

    /**
     * STEP 2: Fetch the final advisory report.
     * Called when user has reviewed and clicks "Get Final Advice".
     */
    async fetchFinalReport(ticker: string, limit: number = 10) {
      if (!this.editableConfig) {
        this.error = "Configuration is not available to generate a report.";
        return;
      }

      this.isLoadingReport = true;
      this.error = null;
      this.finalReport = null; // Clear old report

      try {
        const configToSend = JSON.parse(JSON.stringify(this.editableConfig));
        // Call helper function to clean only the constraints part
        configToSend.constraints = cleanConstraintsForAPI(this.editableConfig.constraints);
        const response = await axios.post(
          `/advisor/quick/${ticker}/full`,
          this.editableConfig, // Send the user-adjusted configuration
          { params: { limit } }
        );
        this.finalReport = response.data;
      } catch (e: any) {
        this.error = e.response?.data?.detail || "Failed to generate the final advisory report.";
        console.error(e);
      } finally {
        this.isLoadingReport = false;
      }
    },

    /**
     * Reset the store state.
     * Will be called when starting a new session or when user leaves the page.
     */
    resetState() {
      this.activeProfile = null;
      this.suggestedConfig = null;
      this.editableConfig = null;
      this.finalReport = null;
      this.isLoadingSuggestion = false;
      this.isLoadingReport = false;
      this.error = null;
    }
  },
});
