// src/stores/advisorStore.ts

import { defineStore } from 'pinia';
import axios from 'axios';
import type { components } from '@/types/api';

// --- TYPE DEFINITIONS ---
// Sử dụng các schema đã được đồng bộ từ backend
type Profile = components['schemas']['ProfileResponse'];
type QuantitativeConfig = components['schemas']['QuantitivePreferencesConfigResponse'];
type AdvisorReport = components['schemas']['AdvisorResponse'];
type Constraints = components['schemas']['PerformanceHardConstraints']

// Định nghĩa cấu trúc của State
interface State {
  activeProfile: Profile | null; // Profile đang được sử dụng cho phiên tư vấn
  suggestedConfig: QuantitativeConfig | null; // Cấu hình gốc do AI gợi ý
  editableConfig: QuantitativeConfig | null; // Cấu hình người dùng đang chỉnh sửa
  finalReport: AdvisorReport | null; // Báo cáo cuối cùng
  
  // Quản lý trạng thái UI chi tiết
  isLoadingSuggestion: boolean;
  isLoadingReport: boolean;
  error: string | null;
}

// --- HELPER FUNCTION (Module hóa) ---
/**
 * Nhận vào một object constraints và chuyển đổi các giá trị chuỗi rỗng ("")
 * trong các tuple thành null để gửi đi cho API.
 * @param originalConstraints - Object constraints gốc từ state.
 * @returns Một object constraints mới đã được làm sạch.
 */
function cleanConstraintsForAPI(originalConstraints: Constraints): Constraints {
  // Tạo một bản sao sâu để không thay đổi object gốc
  const cleaned = JSON.parse(JSON.stringify(originalConstraints));

  for (const key in cleaned) {
    const constraintKey = key as keyof Constraints;
    const value = cleaned[constraintKey];

    if (Array.isArray(value)) {
      // Chuyển đổi "" thành null cho cả min (index 0) và max (index 1)
      value[0] = value[0] === '' ? null : value[0];
      value[1] = value[1] === '' ? null : value[1];
    }
  }
  return cleaned;
}

export const useAdvisorStore = defineStore("advisor", {
  // 1. STATE: Trạng thái ban đầu
  state: (): State => ({
    activeProfile: null,
    suggestedConfig: null,
    editableConfig: null,
    finalReport: null,
    isLoadingSuggestion: false,
    isLoadingReport: false,
    error: null,
  }),

  // 2. ACTIONS: Nơi chứa logic nghiệp vụ
  actions: {
    /**
     * BƯỚC 1: Lấy cấu hình định lượng được gợi ý từ AI.
     * Được gọi khi người dùng chọn một hồ sơ và bắt đầu phiên tư vấn.
     */
    async fetchSuggestedConfig(profile: Profile) {
      this.resetState(); // Dọn dẹp phiên làm việc cũ trước khi bắt đầu
      this.isLoadingSuggestion = true;
      this.error = null;
      this.activeProfile = profile;

      try {
        const response = await axios.post('/personal/suggested_config', profile);
        
        // Lưu kết quả vào cả hai state
        const config: QuantitativeConfig = response.data;

        this.suggestedConfig = config
        // Tạo một bản sao sâu để người dùng chỉnh sửa
        this.editableConfig = JSON.parse(JSON.stringify(config));

      } catch (e: any) {
        this.error = e.response?.data?.detail || "Failed to generate AI suggestions.";
        console.error(e);
      } finally {
        this.isLoadingSuggestion = false;
      }
    },

    /**
     * BƯỚC 2: Lấy báo cáo tư vấn cuối cùng.
     * Được gọi khi người dùng đã xem xét và nhấn "Get Final Advice".
     */
    async fetchFinalReport(ticker: string, limit: number = 10) {
      if (!this.editableConfig) {
        this.error = "Configuration is not available to generate a report.";
        return;
      }

      this.isLoadingReport = true;
      this.error = null;
      this.finalReport = null; // Xóa báo cáo cũ

      try {
        const configToSend = JSON.parse(JSON.stringify(this.editableConfig));
        // Gọi hàm helper để làm sạch chỉ riêng phần constraints
        configToSend.constraints = cleanConstraintsForAPI(this.editableConfig.constraints);
        const response = await axios.post(
          `/advisor/quick/${ticker}/full`,
          this.editableConfig, // Gửi đi cấu hình đã được người dùng tinh chỉnh
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
     * Dọn dẹp trạng thái của store.
     * Sẽ được gọi khi bắt đầu một phiên mới hoặc khi người dùng rời khỏi trang.
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
