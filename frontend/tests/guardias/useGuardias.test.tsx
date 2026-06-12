import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useGuardias } from '@/features/guardias/hooks/useGuardias';
import { getGuardias } from '@/features/guardias/services/guardiaService';

vi.mock('@/features/guardias/services/guardiaService');

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

describe('useGuardias', () => {
  it('fetches guardias for given materiaId', async () => {
    const mockData = { data: [], total: 0, page: 1, per_page: 10, total_pages: 0 };
    vi.mocked(getGuardias).mockResolvedValue(mockData);

    const { result } = renderHook(() => useGuardias('m1', { page: 1 }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockData);
    expect(getGuardias).toHaveBeenCalledWith('m1', { page: 1 });
  });

  it('does not fetch without materiaId', () => {
    vi.mocked(getGuardias).mockResolvedValue({ data: [], total: 0, page: 1, per_page: 10, total_pages: 0 });

    const { result } = renderHook(() => useGuardias('', {}), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(getGuardias).not.toHaveBeenCalled();
  });
});
