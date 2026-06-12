import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { AuthProvider } from '@/features/auth/context/AuthContext';
import AtrasadosPage from '@/features/materias/pages/AtrasadosPage';
import api from '@/shared/services/api';

vi.mock('@/shared/services/api');
const mockedApi = vi.mocked(api);

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/materias/m1/atrasados']}>
        <AuthProvider>
          <Routes>
            <Route path="/materias/:id/atrasados" element={<AtrasadosPage />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('AtrasadosPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('access_token', 'test-token');
    localStorage.setItem('user', JSON.stringify({ id: '1', email: 't@t.com', nombre: 'T', apellido: 'U', rol: 'PROFESOR', tenant_id: 't1' }));
    // Mock api.get to return materia for /materias/:id and empty array for atrasados
    mockedApi.get.mockImplementation((url: string) => {
      if (url.includes('/atrasados')) {
        return Promise.resolve({ data: [] });
      }
      return Promise.resolve({ data: { id: 'm1', nombre: 'M1', cohorte: '2026', comisiones: ['A'], tenant_id: 't1' } });
    });
  });

  it('renders page title in heading', async () => {
    renderPage();
    await waitFor(() => {
      const headings = screen.getAllByText('Atrasados');
      expect(headings.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows empty state for no atrasados', async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText('Todos los alumnos estan al dia')).toBeInTheDocument();
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
