import axios, { type InternalAxiosRequestConfig } from 'axios';
import { enqueueRefresh } from './refreshQueue';

interface RetryConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

const AUTH_ENDPOINTS = ['/auth/login', '/auth/refresh', '/auth/forgot-password', '/auth/reset-password'];

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

function isAuthEndpoint(url: string | undefined): boolean {
  if (!url) return false;
  return AUTH_ENDPOINTS.some((ep) => url.includes(ep));
}

// Request interceptor: attach Authorization token from storage
// Skip auth endpoints — they don't need (and shouldn't carry) a token
api.interceptors.request.use(
  (config) => {
    if (config.url && isAuthEndpoint(config.url)) {
      return config;
    }
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

    // Skip non-401 errors, retry loops, and auth endpoints
    // (401 from /auth/login means bad credentials, not an expired token)
    if (
      !originalRequest ||
      error.response?.status !== 401 ||
      originalRequest._retry ||
      isAuthEndpoint(originalRequest.url)
    ) {
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
  // Defer navigation to next event-loop tick.
  // Calling window.location.href synchronously tears down the DOM while React
  // is still reconciling, which throws DOMException: NotFoundError on removeChild.
  setTimeout(() => {
    window.location.href = '/login';
  }, 0);
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
