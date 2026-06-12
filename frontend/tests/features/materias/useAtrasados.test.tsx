import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useAtrasados, useRanking } from '@/features/materias/services/useAtrasados';
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

describe('useAtrasados', () => {
  it('fetches atrasados without filters', async () => {
    mockedApi.get.mockResolvedValue({ data: [] });
    const { result } = renderHook(() => useAtrasados('m1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.get).toHaveBeenCalledWith('/materias/m1/atrasados');
  });

  it('passes filters as query params', async () => {
    mockedApi.get.mockResolvedValue({ data: [] });
    const { result } = renderHook(() => useAtrasados('m1', { comision: 'A', busqueda: 'Juan' }), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.get).toHaveBeenCalledWith('/materias/m1/atrasados?comision=A&busqueda=Juan');
  });

  it('handles date range filters', async () => {
    mockedApi.get.mockResolvedValue({ data: [] });
    const { result } = renderHook(
      () => useAtrasados('m1', { fecha_desde: '2026-01-01', fecha_hasta: '2026-06-01' }),
      { wrapper: createWrapper() },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.get).toHaveBeenCalledWith('/materias/m1/atrasados?fecha_desde=2026-01-01&fecha_hasta=2026-06-01');
  });
});

describe('useRanking', () => {
  it('fetches ranking for a materia', async () => {
    mockedApi.get.mockResolvedValue({ data: [] });
    const { result } = renderHook(() => useRanking('m1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.get).toHaveBeenCalledWith('/materias/m1/ranking');
  });
});
