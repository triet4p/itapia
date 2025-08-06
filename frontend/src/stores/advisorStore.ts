import { defineStore } from 'pinia';
import axios from 'axios';
import type { components } from '@/types/api';

type AdvisorReport = components['schemas']['AdvisorReportSchema'];

interface State {
  report: AdvisorReport | null;
  explaination: string;
  isLoading: boolean;
  error: string | null;
}

export const useAdvisorStore = defineStore('advisor', {
  state: (): State => ({
    report: null,
    explaination: '',
    isLoading: true,
    error: null,
  }),
  actions: {
    async fetchReport(ticker: string, userId: string) {
      this.$reset();
      this.isLoading = true;
      try {
        const baseUrl = `http://localhost:8000/api/v1/advisor/quick/${ticker}`;
        const apiParams = { user_id: userId };
        const jsonPromise = axios.get(`${baseUrl}/full`, { params: apiParams });
        const textPromise = axios.get(`${baseUrl}/explain`, { params: apiParams });
        const [jsonResponse, textResponse] = await Promise.all([jsonPromise, textPromise]);
        this.report = jsonResponse.data;
        this.explaination = textResponse.data;
      } catch (e: any) {
        this.error = `Could not fetch advisory for ${ticker}. Error: ${e.message}`;
      } finally {
        this.isLoading = false;
      }
    },
  },
});