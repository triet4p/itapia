import { defineStore } from 'pinia';
import axios from 'axios';
import type { components } from '@/types/api';

type RuleResponse = components['schemas']['RuleResponse'];
type RuleExplanation = components['schemas']['ExplainationRuleResponse'];
type NodeSpec = components['schemas']['NodeSpecEntity'];
type SemanticType = components['schemas']['SemanticType'];

interface State {
  rulesList: RuleResponse[];
  nodeDictionary: NodeSpec[];
  currentRule: RuleExplanation | null;
  isLoadingList: boolean;
  isLoadingDetails: boolean;
  error: string | null;
}

export const useRulesStore = defineStore('rules', {
  state: (): State => ({
    rulesList: [],
    nodeDictionary: [], // Sẽ được cache ở đây
    currentRule: null,
    isLoadingList: false,
    isLoadingDetails: false,
    error: null,
  }),
  actions: {
    async fetchRules(purpose: SemanticType = 'ANY') {
      this.isLoadingList = true;
      this.error = null;
      try {
        const response = await axios.get('http://localhost:8000/api/v1/rules', {
          params: { purpose }
        });
        this.rulesList = response.data;
      } catch (e: any) {
        this.error = `Could not fetch rules. Error: ${e.message}`;
      } finally {
        this.isLoadingList = false;
      }
    },
    
    // Action này chỉ gọi API nếu "từ điển" chưa được tải
    async fetchNodeDictionary() {
      if (this.nodeDictionary.length > 0) return; // Đã có dữ liệu, không cần gọi lại

      try {
        const response = await axios.get('http://localhost:8000/api/v1/rules/nodes');
        this.nodeDictionary = response.data;
      } catch (e: any) {
        this.error = `Could not fetch node dictionary. Error: ${e.message}`;
      }
    },
    
    async fetchRuleExplanation(ruleId: string) {
      this.isLoadingDetails = true;
      this.error = null;
      this.currentRule = null;
      try {
        // Luôn đảm bảo "từ điển" node đã được tải
        await this.fetchNodeDictionary();
        
        const response = await axios.get(`http://localhost:8000/api/v1/rules/${ruleId}/explain`);
        this.currentRule = response.data;
      } catch (e: any) {
        this.error = `Could not fetch explanation for ${ruleId}. Error: ${e.message}`;
      } finally {
        this.isLoadingDetails = false;
      }
    }
  }
});