import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useEncuentros } from '@/features/encuentros/hooks/useEncuentros';
import { getEncuentrosAdmin } from '@/features/encuentros/services/encuentroService';

vi.mock('@/features/encuentros/services/encuentroService');

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('useEncuentros', () => {
  it('fetches encuentros with given params', async () => {
    const mockData = { data: [], total: 0, page: 1, per_page: 10, total_pages: 0 };
    vi.mocked(getEncuentrosAdmin).mockResolvedValue(mockData);

    const { result } = renderHook(() => useEncuentros({ page: 1 }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockData);
    expect(getEncuentrosAdmin).toHaveBeenCalledWith({ page: 1 });
  });

  it('returns loading state initially', () => {
    vi.mocked(getEncuentrosAdmin).mockResolvedValue({ data: [], total: 0, page: 1, per_page: 10, total_pages: 0 });

    const { result } = renderHook(() => useEncuentros(), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);
  });
});
