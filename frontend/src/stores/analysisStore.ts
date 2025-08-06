import { defineStore } from "pinia";
import axios from "axios";
import type { components } from "@/types/api";

type AnalysisReport = components['schemas']['QuickCheckAnalysisReport']

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
      this.$reset(); // Reset state trước mỗi lần gọi mới
      this.isLoading = true;
      try {
        const baseUrl = `http://localhost:8000/api/v1/analysis/quick/${ticker}`;
        const jsonPromise = axios.get(`${baseUrl}/full`, { params: queryParams });
        const textPromise = axios.get(`${baseUrl}/explain`, { params: queryParams });
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