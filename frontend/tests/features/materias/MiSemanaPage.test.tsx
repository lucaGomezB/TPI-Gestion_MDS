import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { AuthProvider } from '@/features/auth/context/AuthContext';
import MiSemanaPage from '@/features/materias/pages/MiSemanaPage';
import api from '@/shared/services/api';

vi.mock('@/shared/services/api');
const mockedApi = vi.mocked(api);

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/materias']}>
        <AuthProvider>
          <MiSemanaPage />
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('MiSemanaPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('access_token', 'test-token');
    localStorage.setItem('user', JSON.stringify({ id: '1', email: 't@t.com', nombre: 'T', apellido: 'U', rol: 'PROFESOR', tenant_id: 't1' }));
  });

  it('renders page title', async () => {
    mockedApi.get.mockResolvedValue({ data: [] });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText('Mi Semana')).toBeInTheDocument();
    });
  });

  it('shows PermissionDenied for unauthorized roles', async () => {
    localStorage.setItem('user', JSON.stringify({ id: '1', email: 't@t.com', nombre: 'T', apellido: 'U', rol: 'ALUMNO', tenant_id: 't1' }));
    renderPage();
    await waitFor(() => {
      expect(screen.getByText('Acceso denegado')).toBeInTheDocument();
    });
  });
});
