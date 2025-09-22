/**
 * Rules Store
 * 
 * Manages trading rules, explanations, and node definitions.
 * Handles fetching and caching of rule-related data.
 */

import { defineStore } from 'pinia';
import axios from '@/plugins/axios';
import type { components } from '@/types/api';

type RuleResponse = components['schemas']['RuleResponse'];
type RuleExplanation = components['schemas']['ExplainationRuleResponse'];
type NodeSpec = components['schemas']['NodeResponse'];
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
    nodeDictionary: [], // Will be cached here
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
        const response = await axios.get('/rules', {
          params: { purpose }
        });
        this.rulesList = response.data;
      } catch (e: any) {
        this.error = `Could not fetch rules. Error: ${e.message}`;
      } finally {
        this.isLoadingList = false;
      }
    },
    
    // This action only calls the API if the "dictionary" hasn't been loaded yet
    async fetchNodeDictionary() {
      if (this.nodeDictionary.length > 0) return; // Already have data, no need to call again

      try {
        const response = await axios.get('/rules/nodes');
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
        // Always ensure the node "dictionary" has been loaded
        await this.fetchNodeDictionary();
        
        const response = await axios.get(`/rules/${ruleId}/explain`);
        this.currentRule = response.data;
      } catch (e: any) {
        this.error = `Could not fetch explanation for ${ruleId}. Error: ${e.message}`;
      } finally {
        this.isLoadingDetails = false;
      }
    }
  }
});