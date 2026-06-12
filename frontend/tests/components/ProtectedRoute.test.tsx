import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '../../src/features/auth/context/AuthContext';
import ProtectedRoute from '../../src/components/ProtectedRoute';

function ProtectedPage() {
  return <div data-testid="protected-content">Contenido protegido</div>;
}

function LoginPage() {
  return <div>Página de Inicio de Sesión</div>;
}

function renderProtectedRoute() {
  return render(
    <MemoryRouter initialEntries={['/dashboard']}>
      <AuthProvider>
        <Routes>
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <ProtectedPage />
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<LoginPage />} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders children when user is authenticated', () => {
    localStorage.setItem('access_token', 'valid-token');
    localStorage.setItem(
      'user',
      JSON.stringify({ id: '1', email: 'test@test.com', nombre: 'Test', apellido: 'User', rol: 'ADMIN', tenant_id: 't1' }),
    );

    renderProtectedRoute();
    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
  });

  it('redirects to /login when user is not authenticated', async () => {
    renderProtectedRoute();
    await waitFor(() => {
      expect(screen.getByText('Página de Inicio de Sesión')).toBeInTheDocument();
    });
  });

  it('does not show protected content when unauthenticated', () => {
    renderProtectedRoute();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });
});
