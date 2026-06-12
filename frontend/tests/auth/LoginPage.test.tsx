import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../../src/features/auth/context/AuthContext';
import LoginPage from '../../src/features/auth/pages/LoginPage';

function renderLoginPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <LoginPage />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>,
  );
}

describe('LoginPage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders the login form with email and password fields', () => {
    renderLoginPage();
    expect(screen.getByLabelText(/correo electrónico|email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /iniciar sesión|ingresar/i })).toBeInTheDocument();
  });

  it('shows validation errors when submitting empty form', async () => {
    renderLoginPage();
    fireEvent.click(screen.getByRole('button', { name: /iniciar sesión|ingresar/i }));

    await waitFor(() => {
      expect(screen.getByText(/obligatorio|requerido/i)).toBeInTheDocument();
    });
  });

  it('shows error for invalid email format', async () => {
    renderLoginPage();
    const emailInput = screen.getByLabelText(/correo electrónico|email/i);
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
    fireEvent.click(screen.getByRole('button', { name: /iniciar sesión|ingresar/i }));

    await waitFor(() => {
      expect(screen.getByText(/válido|email/i)).toBeInTheDocument();
    });
  });

  it('renders a link to forgot password', () => {
    renderLoginPage();
    const forgotLink = screen.getByRole('link', { name: /olvidé|contraseña/i });
    expect(forgotLink).toBeInTheDocument();
    expect(forgotLink).toHaveAttribute('href', '/forgot-password');
  });

  it('renders the TOTP fallback link for 2FA', () => {
    renderLoginPage();
    const twoFactorLink = screen.getByText(/código de verificación|código 2fa/i);
    expect(twoFactorLink).toBeInTheDocument();
  });
});
