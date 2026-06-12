import axios, { type InternalAxiosRequestConfig } from 'axios';
import { enqueueRefresh } from './refreshQueue';

interface RetryConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach Authorization token from storage
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

let isRefreshing = false;

// Response interceptor: handle 401 → attempt refresh → retry
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as RetryConfig | undefined;

    // Only handle 401 errors and avoid retry loops
    if (!originalRequest || error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      clearAuthAndRedirect();
      return Promise.reject(error);
    }

    if (isRefreshing) {
      try {
        await waitForRefresh();
        originalRequest.headers.Authorization = `Bearer ${localStorage.getItem('access_token')}`;
        return api(originalRequest);
      } catch {
        return Promise.reject(error);
      }
    }

    isRefreshing = true;
    originalRequest._retry = true;

    try {
      const newAccessToken = await enqueueRefresh(async () => {
        const response = await axios.post('/api/auth/refresh', {
          refresh_token: refreshToken,
        });
        const data = response.data as { access_token: string; refresh_token: string };
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        return data.access_token;
      });

      originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
      return api(originalRequest);
    } catch {
      clearAuthAndRedirect();
      return Promise.reject(error);
    } finally {
      isRefreshing = false;
    }
  },
);

function clearAuthAndRedirect(): void {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  window.location.href = '/login';
}

function waitForRefresh(): Promise<void> {
  return new Promise<void>((resolve) => {
    const check = setInterval(() => {
      if (!isRefreshing) {
        clearInterval(check);
        resolve();
      }
    }, 100);
  });
}

export default api;
