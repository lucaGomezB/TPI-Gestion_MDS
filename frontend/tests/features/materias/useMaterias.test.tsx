import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useMaterias, useMateria } from '@/features/materias/services/useMaterias';
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

describe('useMaterias', () => {
  it('fetches materias list', async () => {
    const mockData = [{ id: 'm1', nombre: 'Matematica', cohorte: '2026', comisiones: ['A'], tenant_id: 't1' }];
    mockedApi.get.mockResolvedValue({ data: mockData });

    const { result } = renderHook(() => useMaterias(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith('/materias');
    expect(result.current.data).toEqual(mockData);
  });
});

describe('useMateria', () => {
  it('fetches a single materia by id', async () => {
    const mockData = { id: 'm1', nombre: 'Matematica', cohorte: '2026', comisiones: ['A'], tenant_id: 't1' };
    mockedApi.get.mockResolvedValue({ data: mockData });

    const { result } = renderHook(() => useMateria('m1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.get).toHaveBeenCalledWith('/materias/m1');
    expect(result.current.data).toEqual(mockData);
  });
});
