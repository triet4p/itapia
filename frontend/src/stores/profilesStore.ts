// src/stores/profileStore.ts
import { defineStore } from 'pinia';
import axios from '@/plugins/axios'; // Import axios đã được cấu hình
import type { components } from '@/types/api';
import { useAuthStore } from './authStore'; // Import authStore

type Profile = components['schemas']['ProfileResponse'];
type ProfileCreate = components['schemas']['ProfileCreateRequest'];
type ProfileUpdate = components['schemas']['ProfileUpdateRequest'];

interface State {
  profiles: Profile[];
  currentProfile: Profile | null;
  isLoadingList: boolean;
  isLoadingDetails: boolean;
  error: string | null;
}

export const useProfileStore = defineStore('profile', {
  state: (): State => ({
    profiles: [],
    currentProfile: null,
    isLoadingList: false,
    isLoadingDetails: false,
    error: null,
  }),
  actions: {
    // Lấy danh sách tất cả profile
    async fetchProfiles() {
      // 1. Kiểm tra xem người dùng đã đăng nhập chưa từ authStore
      const authStore = useAuthStore();
      if (!authStore.isLoggedIn) return; // Không làm gì nếu chưa đăng nhập

      this.isLoadingList = true;
      this.error = null;
      try {
        // 2. Không cần thêm header nữa! Interceptor sẽ tự làm.
        const response = await axios.get('/profiles');
        this.profiles = response.data;
      } catch (e: any) {
        this.error = "Failed to fetch profiles.";
        console.error(e);
      } finally {
        this.isLoadingList = false;
      }
    },

    // Lấy chi tiết một profile
    async fetchProfileDetails(profileId: string) {
      this.isLoadingDetails = true;
      this.currentProfile = null;
      this.error = null;
      try {
        // 3. Không cần thêm header
        const response = await axios.get(`/profiles/${profileId}`);
        this.currentProfile = response.data;
      } catch (e: any) {
        this.error = "Failed to fetch profile details.";
        console.error(e);
      } finally {
        this.isLoadingDetails = false;
      }
    },

    // Tạo profile mới
    async createProfile(profileData: ProfileCreate) {
      try {
        // 4. Không cần thêm header
        const response = await axios.post('/profiles', profileData);
        this.profiles.unshift(response.data);
        return true;
      } catch (e: any) {
        this.error = "Failed to create profile.";
        console.error(e);
        return false;
      }
    },
    
    // --- MỚI: Action để cập nhật profile ---
    async updateProfile(profileId: string, profileData: ProfileUpdate) {
      this.error = null;
      try {
        // Gửi request PUT đến API
        const response = await axios.put(`/profiles/${profileId}`, profileData);
        
        // Cập nhật lại state cục bộ để giao diện thay đổi ngay lập tức
        
        // 1. Cập nhật trong danh sách `profiles`
        const index = this.profiles.findIndex(p => p.profile_id === profileId);
        if (index !== -1) {
          this.profiles[index] = response.data;
        }

        // 2. Cập nhật `currentProfile` nếu nó đang được hiển thị
        if (this.currentProfile?.profile_id === profileId) {
          this.currentProfile = response.data;
        }
        
        return true; // Báo thành công
      } catch (e: any) {
        this.error = "Failed to update profile.";
        console.error(e);
        return false; // Báo thất bại
      }
    },

    // --- MỚI: Action để xóa profile ---
    async deleteProfile(profileId: string) {
      this.error = null;
      try {
        // Gửi request DELETE đến API
        await axios.delete(`/profiles/${profileId}`);

        // Xóa profile khỏi danh sách `profiles` trong state
        this.profiles = this.profiles.filter(p => p.profile_id !== profileId);

        // Nếu profile đang được xem chi tiết bị xóa, hãy xóa nó đi
        if (this.currentProfile?.profile_id === profileId) {
          this.currentProfile = null;
        }
        
        return true; // Báo thành công
      } catch (e: any) {
        this.error = "Failed to delete profile.";
        console.error(e);
        return false; // Báo thất bại
      }
    }
  },
});