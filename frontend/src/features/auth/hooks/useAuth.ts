import { useMutation } from '@tanstack/react-query';
import { login, logout, refresh } from '../services/authService';
import type { LoginRequest, LoginResponse, RefreshRequest } from '../types';

export { useAuth } from '../context/AuthContext';

export function useLogin() {
  return useMutation<LoginResponse, Error, LoginRequest>({
    mutationFn: login,
  });
}

export function useLogout() {
  return useMutation<void, Error, void>({
    mutationFn: logout,
  });
}

export function useRefreshToken() {
  return useMutation({
    mutationFn: (data: RefreshRequest) => refresh(data),
  });
}
