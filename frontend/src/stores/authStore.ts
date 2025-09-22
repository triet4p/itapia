// src/stores/authStore.ts
/**
 * Authentication Store
 * 
 * Manages user authentication state, login/logout functionality,
 * and user profile information.
 */

import { defineStore } from 'pinia';
import axios from '@/plugins/axios';
import router from '@/router'; // Directly import router instance
import type { components } from '@/types/api';

type UserInfo = components['schemas']['UserResponse'];

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
     * Initiate the login flow
     */
    async redirectToGoogle() {
      if (this.isLoading) return;
      this.isLoading = true;
      try {
        const response = await axios.get('/auth/google/login');
        window.location.href = response.data.authorization_url;
      } catch (error) {
        console.error("Failed to get Google authorization URL", error);
        this.isLoading = false;
      }
    },

    /**
     * NEW: Called from the callback page after successful login
     */
    async handleLoginSuccess(token: string) {
      // 1. Save token to state and localStorage
      this.token = token;
      localStorage.setItem('authToken', token);

      // 2. Call API to get user information
      await this.fetchCurrentUser();
    },
    
    /**
     * NEW: Call API /users/me to get user info
     */
    async fetchCurrentUser() {
      if (!this.token) return;

      try {
        // Configure Axios to send token in header
        const response = await axios.get('/users/me');
        this.user = response.data;
      } catch (error) {
        console.error("Failed to fetch user info. Token might be invalid.", error);
        // If token is invalid, logout
        this.logout();
      }
    },

    /**
     * Logout user
     */
    logout() {
      this.token = null;
      this.user = null;
      localStorage.removeItem('authToken');
      // Use imported router to ensure it works everywhere
      router.push('/login');
    },

    /**
     * NEW: Called when the application starts
     */
    async initializeAuth() {
      if (this.token) {
        console.log("Token found in storage, fetching user info...");
        await this.fetchCurrentUser();
      }
    }
  },
});