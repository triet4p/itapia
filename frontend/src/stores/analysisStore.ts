/**
 * Analysis Store
 * 
 * Manages state and logic for market analysis functionality.
 * Handles fetching and storing analysis reports and explanations.
 */

import { defineStore } from "pinia";
import axios from "@/plugins/axios";
import type { components } from "@/types/api";

type AnalysisReport = components['schemas']['QuickCheckReportResponse'];

interface State {
  report: AnalysisReport | null;
  explaination: string;
  isLoading: boolean;
  error: string | null;
};

export const useAnalysisStore = defineStore('analysis', {
  state: (): State => ({
    report: null,
    explaination: '',
    isLoading: true,
    error: null
  }), 
  actions: {
    async fetchReport(ticker: string, queryParams: Record<string, any>) {
      this.$reset(); // Reset state before each new call
      this.isLoading = true;
      try {
        const jsonPromise = axios.get(`/analysis/quick/${ticker}/full`, { params: queryParams });
        const textPromise = axios.get(`/analysis/quick/${ticker}/explain`, { params: queryParams });
        const [jsonResponse, textResponse] = await Promise.all([jsonPromise, textPromise]);
        this.report = jsonResponse.data;
        this.explaination = textResponse.data;
      } catch (e: any) {
        this.error = `Could not fetch analysis for ${ticker}. Error: ${e.message}`;
      } finally {
        this.isLoading = false;
      }
    },
  },
});