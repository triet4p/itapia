// src/plugins/axios.ts
/**
 * Axios Configuration Plugin
 * 
 * Configures axios with default settings and interceptors for API requests.
 * Sets up request and response interceptors for authentication token handling
 * and automatic logout on 401 responses.
 */

import axios from 'axios';
import { useAuthStore } from '@/stores/authStore';

// Configure default values for axios
axios.defaults.baseURL = import.meta.env.VITE_BACKEND_URL + import.meta.env.VITE_BACKEND_API_BASE_ROUTE; // Set base URL
axios.defaults.headers.common['Content-Type'] = 'application/json';

// --- Axios Request Interceptor ---
// This is the "gatekeeper" for outgoing requests
axios.interceptors.request.use(
  (config) => {
    // Initialize authStore to get token
    // Note: Not using storeToRefs here
    const authStore = useAuthStore();
    const token = authStore.token; // Get token from authStore state

    // If there's a token, attach it to the Authorization header
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config; // Return the modified config
  },
  (error) => {
    // Handle errors if any
    return Promise.reject(error);
  }
);

// (Optional) You can also add interceptor for responses here
// to handle common errors like 401 Unauthorized
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      // If we receive a 401 error (invalid/expired token)
      const authStore = useAuthStore();
      authStore.logout(); // Automatically logout the user
    }
    return Promise.reject(error);
  }
);

export default axios;