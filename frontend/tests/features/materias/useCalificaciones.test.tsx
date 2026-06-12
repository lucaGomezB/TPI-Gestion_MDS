import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import {
  useCalificaciones,
  useUmbral,
  useUpdateUmbral,
  useImportarCalificaciones,
  useConfirmImport,
  useVaciarCalificaciones,
} from '@/features/materias/services/useCalificaciones';
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

describe('useCalificaciones', () => {
  it('fetches calificaciones for a materia', async () => {
    mockedApi.get.mockResolvedValue({ data: [] });
    const { result } = renderHook(() => useCalificaciones('m1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.get).toHaveBeenCalledWith('/materias/m1/calificaciones');
  });
});

describe('useUmbral', () => {
  it('fetches umbral for a materia', async () => {
    mockedApi.get.mockResolvedValue({ data: { umbral_pct: 60, materia_id: 'm1' } });
    const { result } = renderHook(() => useUmbral('m1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.get).toHaveBeenCalledWith('/materias/m1/calificaciones/umbral');
    expect(result.current.data?.umbral_pct).toBe(60);
  });
});

describe('useUpdateUmbral', () => {
  it('posts new umbral value', async () => {
    mockedApi.post.mockResolvedValue({ data: { umbral_pct: 70, materia_id: 'm1' } });
    const { result } = renderHook(() => useUpdateUmbral('m1'), { wrapper: createWrapper() });
    result.current.mutate(70);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.post).toHaveBeenCalledWith('/materias/m1/calificaciones/umbral', { umbral_pct: 70 });
  });
});

describe('useImportarCalificaciones', () => {
  it('uploads a file via FormData', async () => {
    mockedApi.post.mockResolvedValue({ data: { message: 'ok' } });
    const file = new File(['test'], 'test.xlsx');
    const { result } = renderHook(() => useImportarCalificaciones('m1'), { wrapper: createWrapper() });
    result.current.mutate(file);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/materias/m1/calificaciones/importar',
      expect.any(FormData),
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
  });
});

describe('useConfirmImport', () => {
  it('sends selected activities to confirm', async () => {
    mockedApi.post.mockResolvedValue({ data: { message: 'ok' } });
    const { result } = renderHook(() => useConfirmImport('m1'), { wrapper: createWrapper() });
    result.current.mutate(['TP1', 'TP2']);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.post).toHaveBeenCalledWith('/materias/m1/calificaciones/importar/confirmar', {
      actividades: ['TP1', 'TP2'],
    });
  });
});

describe('useVaciarCalificaciones', () => {
  it('calls delete endpoint', async () => {
    mockedApi.delete.mockResolvedValue({});
    const { result } = renderHook(() => useVaciarCalificaciones('m1'), { wrapper: createWrapper() });
    result.current.mutate(undefined);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.delete).toHaveBeenCalledWith('/materias/m1/calificaciones');
  });
});
