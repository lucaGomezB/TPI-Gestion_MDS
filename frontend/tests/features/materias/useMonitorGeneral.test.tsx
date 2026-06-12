import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useMonitorGeneral, useExportMonitorGeneral } from '@/features/materias/services/useMonitorGeneral';
import api from '@/shared/services/api';

vi.mock('@/shared/services/api');
const mockedApi = vi.mocked(api);

function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('useMonitorGeneral', () => {
  it('fetches all data without filters', async () => {
    mockedApi.get.mockResolvedValue({ data: [] });
    const { result } = renderHook(() => useMonitorGeneral(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.get).toHaveBeenCalledWith('/admin/materias/monitor-general');
  });

  it('passes filters as query params', async () => {
    mockedApi.get.mockResolvedValue({ data: [] });
    const { result } = renderHook(
      () => useMonitorGeneral({ materia_id: 'm1', regional: 'CABA', comision: 'A', busqueda: 'Mate', status: 'con_atrasados' }),
      { wrapper: createWrapper() },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.get).toHaveBeenCalledWith(
      '/admin/materias/monitor-general?materia_id=m1&regional=CABA&comision=A&busqueda=Mate&status=con_atrasados',
    );
  });

  it('omits status when set to todos', async () => {
    mockedApi.get.mockResolvedValue({ data: [] });
    const { result } = renderHook(
      () => useMonitorGeneral({ status: 'todos' }),
      { wrapper: createWrapper() },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.get).toHaveBeenCalledWith('/admin/materias/monitor-general');
  });
});

describe('useExportMonitorGeneral', () => {
  it('returns a function', async () => {
    mockedApi.get.mockResolvedValue({ data: new Blob() });
    const { result } = renderHook(() => useExportMonitorGeneral(), { wrapper: createWrapper() });
    expect(typeof result.current).toBe('function');
  });
});
