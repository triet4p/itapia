// src/plugins/axios.ts

import axios from 'axios';
import { useAuthStore } from '@/stores/authStore';

// Cấu hình các giá trị mặc định cho axios
axios.defaults.baseURL = import.meta.env.VITE_API_BASE_URL; // Đặt base URL ở đây
axios.defaults.headers.common['Content-Type'] = 'application/json';

// --- Axios Request Interceptor ---
// Đây là "người gác cổng" cho các request gửi đi.
axios.interceptors.request.use(
  (config) => {
    // Khởi tạo authStore để lấy token
    // Lưu ý: Không dùng storeToRefs ở đây
    const authStore = useAuthStore();
    const token = authStore.token; // Lấy token từ state của authStore

    // Nếu có token, đính kèm nó vào header Authorization
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config; // Trả về config đã được sửa đổi
  },
  (error) => {
    // Xử lý lỗi nếu có
    return Promise.reject(error);
  }
);

// (Tùy chọn) Bạn cũng có thể thêm interceptor cho response ở đây
// để xử lý các lỗi chung như 401 Unauthorized
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      // Nếu nhận được lỗi 401 (token không hợp lệ/hết hạn)
      const authStore = useAuthStore();
      authStore.logout(); // Tự động logout người dùng
    }
    return Promise.reject(error);
  }
);

export default axios;