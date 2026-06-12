import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useUploadPadron, useReplacePadron } from '@/features/materias/services/usePadron';
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

describe('useUploadPadron', () => {
  it('uploads padron file via POST', async () => {
    const mockResult = { total_filas: 100, importadas: 95, duplicadas: 5, errores: [] };
    mockedApi.post.mockResolvedValue({ data: mockResult });
    const file = new File(['test'], 'padron.xlsx');

    const { result } = renderHook(() => useUploadPadron('m1'), { wrapper: createWrapper() });
    result.current.mutate(file);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.post).toHaveBeenCalledWith(
      '/materias/m1/padron',
      expect.any(FormData),
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
    expect(result.current.data).toEqual(mockResult);
  });
});

describe('useReplacePadron', () => {
  it('replaces padron file via PUT', async () => {
    const mockResult = { total_filas: 50, importadas: 50, duplicadas: 0, errores: [] };
    mockedApi.put.mockResolvedValue({ data: mockResult });
    const file = new File(['test'], 'padron.xlsx');

    const { result } = renderHook(() => useReplacePadron('m1'), { wrapper: createWrapper() });
    result.current.mutate(file);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.put).toHaveBeenCalledWith(
      '/materias/m1/padron',
      expect.any(FormData),
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
    expect(result.current.data).toEqual(mockResult);
  });
});
