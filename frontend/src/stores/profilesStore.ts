// src/stores/profileStore.ts
/**
 * Profile Store
 * 
 * Manages user investment profiles including creation, retrieval,
 * updating, and deletion operations.
 */

import { defineStore } from 'pinia';
import axios from '@/plugins/axios'; // Import configured axios
import type { components } from '@/types/api';

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

  getters: {
    defaultProfile: (state): Profile | undefined => {
      return state.profiles.find(p => p.is_default);
    },
  },

  actions: {
    // Fetch list of all profiles
    async fetchProfiles() {

      this.isLoadingList = true;
      this.error = null;
      try {
        // 2. No need to add headers anymore! Interceptor will do it automatically.
        const response = await axios.get('/profiles');
        this.profiles = response.data;
      } catch (e: any) {
        this.error = e.response?.data?.details || "Failed to fetch profiles.";
        console.error(e);
      } finally {
        this.isLoadingList = false;
      }
    },

    // Fetch details of a specific profile
    async fetchProfileDetails(profileId: string) {
      this.isLoadingDetails = true;
      this.currentProfile = null;
      this.error = null;
      try {
        // 3. No need to add headers
        const response = await axios.get(`/profiles/${profileId}`);
        this.currentProfile = response.data;
      } catch (e: any) {
        this.error = e.response?.data?.detail || "Failed to fetch profile details.";
        console.error(e);
      } finally {
        this.isLoadingDetails = false;
      }
    },

    // Create a new profile
    async createProfile(profileData: ProfileCreate): Promise<boolean> {
      this.error = null;
      try {
        // 4. No need to add headers
        const response = await axios.post('/profiles', profileData);
        this.profiles.unshift(response.data);
        return true;
      } catch (e: any) {
        this.error = e.response?.data?.detail || "Failed to create profile.";
        console.error(e);
        return false;
      }
    },
    
    // --- NEW: Action to update a profile ---
    async updateProfile(profileId: string, profileData: ProfileUpdate): Promise<boolean> {
      this.error = null;
      try {
        // Send PUT request to API
        const response = await axios.put(`/profiles/${profileId}`, profileData);
        
        // Update local state immediately for UI changes
        
        // 1. Update in the `profiles` list
        const index = this.profiles.findIndex(p => p.profile_id === profileId);
        if (index !== -1) {
          this.profiles[index] = response.data;
        }

        // 2. Update `currentProfile` if it's currently being displayed
        if (this.currentProfile?.profile_id === profileId) {
          this.currentProfile = response.data;
        }
        
        return true; // Report success
      } catch (e: any) {
        this.error = e.response?.data?.detail || "Failed to update profile.";
        console.error(e);
        return false; // Report failure
      }
    },

    // --- NEW: Action to delete a profile ---
    async deleteProfile(profileId: string): Promise<boolean> {
      this.error = null;
      try {
        // Send DELETE request to API
        await axios.delete(`/profiles/${profileId}`);

        // Remove profile from the `profiles` list in state
        this.profiles = this.profiles.filter(p => p.profile_id !== profileId);

        // If the profile being viewed in detail is deleted, clear it
        if (this.currentProfile?.profile_id === profileId) {
          this.currentProfile = null;
        }
        
        return true; // Report success
      } catch (e: any) {
        this.error = e.response?.data?.detail || "Failed to delete profile.";
        console.error(e);
        return false; // Report failure
      }
    }
  },
});