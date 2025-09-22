/**
 * App Store
 * 
 * Main application store for global state management.
 * Contains general application-level state and settings.
 */

// Utility imports
import { defineStore } from 'pinia';

export const useAppStore = defineStore('app', {
  state: () => ({
    // Application-wide state properties can be defined here
  }),
});
