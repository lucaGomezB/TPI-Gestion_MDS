import { render, screen, renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AuthProvider, useAuth } from '../../src/features/auth/context/AuthContext';
import * as authService from '../../src/features/auth/services/authService';
import type { User } from '../../src/features/auth/types';

const mockUser: User = {
  id: '1',
  email: 'test@test.com',
  nombre: 'Test',
  apellido: 'User',
  rol: 'ADMIN',
  tenant_id: 'tenant-1',
};

const mockLoginResponse = {
  access_token: 'access-123',
  refresh_token: 'refresh-123',
  user: mockUser,
};

function renderProvider() {
  return render(
    <AuthProvider>
      <div>Provider rendered</div>
    </AuthProvider>,
  );
}

function renderUseAuth() {
  return renderHook(() => useAuth(), { wrapper: AuthProvider });
}

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('renders AuthProvider without crashing', () => {
    renderProvider();
    expect(screen.getByText('Provider rendered')).toBeInTheDocument();
  });

  it('starts with isLoading false and no user when no tokens exist', () => {
    const { result } = renderUseAuth();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it('loads user from localStorage when access_token exists', () => {
    localStorage.setItem('access_token', 'existing-token');
    localStorage.setItem('user', JSON.stringify(mockUser));

    const { result } = renderUseAuth();
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isLoading).toBe(false);
  });

  it('calls login and updates state on successful login', async () => {
    const loginSpy = vi.spyOn(authService, 'login').mockResolvedValue(mockLoginResponse);

    const { result } = renderUseAuth();

    await act(async () => {
      await result.current.login({ email: 'test@test.com', password: 'password' });
    });

    expect(loginSpy).toHaveBeenCalledWith({ email: 'test@test.com', password: 'password' });
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual(mockUser);
    expect(localStorage.getItem('access_token')).toBe('access-123');
    expect(localStorage.getItem('refresh_token')).toBe('refresh-123');
  });

  it('calls logout, clears state and localStorage', async () => {
    const logoutSpy = vi.spyOn(authService, 'logout').mockResolvedValue(undefined);
    localStorage.setItem('access_token', 'access-123');
    localStorage.setItem('refresh_token', 'refresh-123');
    localStorage.setItem('user', JSON.stringify(mockUser));

    const { result } = renderUseAuth();

    await act(async () => {
      await result.current.logout();
    });

    expect(logoutSpy).toHaveBeenCalled();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
  });

  it('throws error when useAuth is used outside AuthProvider', () => {
    expect(() => {
      renderHook(() => useAuth());
    }).toThrow('useAuth debe usarse dentro de un AuthProvider');
  });
});
