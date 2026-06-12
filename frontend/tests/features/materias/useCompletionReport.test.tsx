import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import {
  useCompletionReport,
  useUploadCompletionReport,
  useExportCompletionReport,
} from '@/features/materias/services/useCompletionReport';
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

describe('useCompletionReport', () => {
  it('fetches completion report for a materia', async () => {
    const mockData = {
      materia_id: 'm1', total_alumnos: 30, total_pendientes: 5, total_completados: 25, items: [],
    };
    mockedApi.get.mockResolvedValue({ data: mockData });
    const { result } = renderHook(() => useCompletionReport('m1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.get).toHaveBeenCalledWith('/materias/m1/completion-report');
    expect(result.current.data?.total_pendientes).toBe(5);
  });
});

describe('useUploadCompletionReport', () => {
  it('uploads completion report file via POST', async () => {
    const mockResult = {
      materia_id: 'm1', total_alumnos: 30, total_pendientes: 5, total_completados: 25, items: [],
    };
    mockedApi.post.mockResolvedValue({ data: mockResult });
    const file = new File(['test'], 'report.xlsx');

    const { result } = renderHook(() => useUploadCompletionReport('m1'), { wrapper: createWrapper() });
    result.current.mutate(file);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedApi.post).toHaveBeenCalledWith(
      '/materias/m1/completion-report',
      expect.any(FormData),
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
    expect(result.current.data?.total_completados).toBe(25);
  });
});

describe('useExportCompletionReport', () => {
  it('returns a function', async () => {
    mockedApi.get.mockResolvedValue({ data: new Blob() });
    const { result } = renderHook(() => useExportCompletionReport(), { wrapper: createWrapper() });
    expect(typeof result.current).toBe('function');
  });
});
