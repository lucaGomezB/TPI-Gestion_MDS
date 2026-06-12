import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useSeguimiento } from '@/features/materias/services/useSeguimiento';
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

describe('useSeguimiento', () => {
  it('fetches seguimiento without filters', async () => {
    mockedApi.get.mockResolvedValue({ data: [] });
    const { result } = renderHook(() => useSeguimiento('m1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.get).toHaveBeenCalledWith('/materias/m1/seguimiento');
  });

  it('passes all filters as query params', async () => {
    mockedApi.get.mockResolvedValue({ data: [] });
    const { result } = renderHook(
      () => useSeguimiento('m1', { busqueda: 'Juan', comision: 'A', actividad: 'TP1', regional: 'CABA', minimo_actividades: 3 }),
      { wrapper: createWrapper() },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.get).toHaveBeenCalledWith('/materias/m1/seguimiento?busqueda=Juan&comision=A&actividad=TP1&regional=CABA&minimo_actividades=3');
  });

  it('skips undefined filter params', async () => {
    mockedApi.get.mockResolvedValue({ data: [] });
    const { result } = renderHook(
      () => useSeguimiento('m1', { comision: 'A' }),
      { wrapper: createWrapper() },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.get).toHaveBeenCalledWith('/materias/m1/seguimiento?comision=A');
  });
});
