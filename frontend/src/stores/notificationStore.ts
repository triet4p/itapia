/**
 * Notification Store
 * 
 * Manages application notifications and toast messages.
 * Provides a centralized way to display feedback to users.
 */

import { defineStore } from "pinia";

interface State {
  message: string;
  color: string;
  visible: boolean;
  timeout: number;
}

export const useNotificationStore = defineStore('notification', {
  state: (): State => ({
    message: '',
    color: 'info',
    visible: false,
    timeout: 5000, // 5 seconds
  }),
  actions: {
    showNotification(payload: { message: string, color?: string, timeout?: number }) {
      this.message = payload.message;
      this.color = payload.color || 'info';
      this.timeout = payload.timeout || 5000;
      this.visible = true;
    },
  },
});