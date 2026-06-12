import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useConvocatorias } from '@/features/coloquios/hooks/useConvocatorias';
import { getConvocatorias } from '@/features/coloquios/services/coloquioService';

vi.mock('@/features/coloquios/services/coloquioService');

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

describe('useConvocatorias', () => {
  it('fetches convocatorias with materiaId', async () => {
    vi.mocked(getConvocatorias).mockResolvedValue([]);

    const { result } = renderHook(() => useConvocatorias('m1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(getConvocatorias).toHaveBeenCalledWith({ materia_id: 'm1' });
  });
});
