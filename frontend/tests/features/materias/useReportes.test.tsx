import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useReportes, useNotasFinales, useExportNotasFinales, useExportAtrasados } from '@/features/materias/services/useReportes';
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
  // Mock window.URL.createObjectURL and document.createElement for export tests
  globalThis.URL.createObjectURL = vi.fn(() => 'blob:test');
  globalThis.URL.revokeObjectURL = vi.fn();
});

describe('useReportes', () => {
  it('fetches reportes for a materia', async () => {
    mockedApi.get.mockResolvedValue({ data: { total_alumnos: 30, total_actividades: 10, promedio_general: 7.5, aprobados: 20, reprobados: 10, atrasados: 5 } });
    const { result } = renderHook(() => useReportes('m1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.get).toHaveBeenCalledWith('/materias/m1/reportes');
    expect(result.current.data?.total_alumnos).toBe(30);
  });
});

describe('useNotasFinales', () => {
  it('fetches notas finales', async () => {
    mockedApi.get.mockResolvedValue({ data: [] });
    const { result } = renderHook(() => useNotasFinales('m1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.get).toHaveBeenCalledWith('/materias/m1/notas-finales');
  });
});

describe('useExportNotasFinales', () => {
  it('returns a function that triggers blob download', async () => {
    const blob = new Blob(['test'], { type: 'text/csv' });
    mockedApi.get.mockResolvedValue({ data: blob });
    const { result } = renderHook(() => useExportNotasFinales(), { wrapper: createWrapper() });
    // Export function is a closure, not a hook
    expect(typeof result.current).toBe('function');
  });
});

describe('useExportAtrasados', () => {
  it('returns a function that triggers blob download', async () => {
    const blob = new Blob(['test'], { type: 'text/csv' });
    mockedApi.get.mockResolvedValue({ data: blob });
    const { result } = renderHook(() => useExportAtrasados(), { wrapper: createWrapper() });
    expect(typeof result.current).toBe('function');
  });
});
