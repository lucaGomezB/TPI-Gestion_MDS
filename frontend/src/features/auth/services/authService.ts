import api from '@/shared/services/api';
import type { LoginRequest, LoginResponse, RefreshRequest, RefreshResponse } from '../types';

export async function login(data: LoginRequest): Promise<LoginResponse> {
  const response = await api.post<LoginResponse>('/auth/login', data);
  return response.data;
}

export async function logout(): Promise<void> {
  await api.post('/auth/logout');
}

export async function refresh(data: RefreshRequest): Promise<RefreshResponse> {
  const response = await api.post<RefreshResponse>('/auth/refresh', data);
  return response.data;
}
