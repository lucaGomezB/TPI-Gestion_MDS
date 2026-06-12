import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { AuthProvider } from '@/features/auth/context/AuthContext';
import MateriaDetailPage from '@/features/materias/pages/MateriaDetailPage';
import api from '@/shared/services/api';

vi.mock('@/shared/services/api');
const mockedApi = vi.mocked(api);

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/materias/m1']}>
        <AuthProvider>
          <Routes>
            <Route path="/materias/:id" element={<MateriaDetailPage />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('MateriaDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('access_token', 'test-token');
    localStorage.setItem('user', JSON.stringify({ id: '1', email: 't@t.com', nombre: 'T', apellido: 'U', rol: 'PROFESOR', tenant_id: 't1' }));
  });

  it('renders loading state initially', () => {
    mockedApi.get.mockResolvedValue({ data: { id: 'm1', nombre: 'Matematica', cohorte: '2026', comisiones: ['A'], tenant_id: 't1' } });
    renderPage();
    expect(screen.getByText('Materias')).toBeInTheDocument();
  });

  it('shows PermissionDenied for unauthorized roles', async () => {
    localStorage.setItem('user', JSON.stringify({ id: '1', email: 't@t.com', nombre: 'T', apellido: 'U', rol: 'ALUMNO', tenant_id: 't1' }));
    renderPage();
    await waitFor(() => {
      expect(screen.getByText('Acceso denegado')).toBeInTheDocument();
    });
  });
});
