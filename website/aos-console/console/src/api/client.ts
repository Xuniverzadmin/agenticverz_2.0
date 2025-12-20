import axios, { InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/stores/authStore';

// Use relative URL in production (same origin), empty for same-origin requests
const API_BASE = import.meta.env.VITE_API_BASE || '';
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '15000', 10);

export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth headers to all requests
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token;
  const tenantId = useAuthStore.getState().tenantId;

  if (token) {
    // JWT tokens start with 'ey' (base64 JSON header)
    // API keys are hex strings - always use X-API-Key header
    if (token.startsWith('ey')) {
      config.headers['Authorization'] = `Bearer ${token}`;
    } else {
      config.headers['X-API-Key'] = token;
    }
  }
  if (tenantId) {
    config.headers['X-Tenant-ID'] = tenantId;
  }

  return config;
});

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      const loginUrl = import.meta.env.VITE_AUTH_LOGIN_URL || '/console/login';
      window.location.href = loginUrl;
    }
    return Promise.reject(error);
  }
);

export default apiClient;
