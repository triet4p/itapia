// src/stores/authStore.ts

import { defineStore } from 'pinia';
import axios from 'axios';
import router from '@/router'; // Import trực tiếp router instance
import type { components } from '@/types/api';

type UserInfo = components['schemas']['UserEntity'];

interface AuthState {
  user: UserInfo | null;
  token: string | null;
  isLoading: boolean;
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    token: localStorage.getItem('authToken'),
    isLoading: false,
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    userName: (state) => state.user?.full_name || 'Guest',
  },

  actions: {
    /**
     * Bắt đầu luồng đăng nhập
     */
    async redirectToGoogle() {
      if (this.isLoading) return;
      this.isLoading = true;
      try {
        const response = await axios.get('http://localhost:8000/api/v1/auth/google/login');
        window.location.href = response.data.authorization_url;
      } catch (error) {
        console.error("Failed to get Google authorization URL", error);
        this.isLoading = false;
      }
    },

    /**
     * MỚI: Được gọi từ trang callback sau khi đăng nhập thành công
     */
    async handleLoginSuccess(token: string) {
      // 1. Lưu token vào state và localStorage
      this.token = token;
      localStorage.setItem('authToken', token);

      // 2. Gọi API để lấy thông tin người dùng
      await this.fetchCurrentUser();
    },
    
    /**
     * MỚI: Gọi API /users/me để lấy thông tin user
     */
    async fetchCurrentUser() {
      if (!this.token) return;

      try {
        // Cấu hình Axios để gửi token trong header
        const response = await axios.get('http://localhost:8000/api/v1/users/me', {
          headers: {
            Authorization: `Bearer ${this.token}`,
          },
        });
        this.user = response.data;
      } catch (error) {
        console.error("Failed to fetch user info. Token might be invalid.", error);
        // Nếu token không hợp lệ, hãy logout
        this.logout();
      }
    },

    /**
     * Đăng xuất
     */
    logout() {
      this.token = null;
      this.user = null;
      localStorage.removeItem('authToken');
      // Dùng router đã import để đảm bảo hoạt động ở mọi nơi
      router.push('/login');
    },

    /**
     * MỚI: Được gọi khi ứng dụng khởi động
     */
    async initializeAuth() {
      if (this.token) {
        console.log("Token found in storage, fetching user info...");
        await this.fetchCurrentUser();
      }
    }
  },
});