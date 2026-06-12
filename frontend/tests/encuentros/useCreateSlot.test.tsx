import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useCreateSlot } from '@/features/encuentros/hooks/useCreateSlot';
import { createSlot } from '@/features/encuentros/services/encuentroService';

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

describe('useCreateSlot', () => {
  it('calls createSlot service on mutation', async () => {
    const payload = {
      materia_id: 'm1',
      titulo: 'Slot Test',
      dia_semana: 'Lunes' as const,
      hora: '10:00',
      fecha_inicio: '2026-06-01',
      cant_semanas: 4,
    };
    vi.mocked(createSlot).mockResolvedValue({ id: 's1' });

    const { result } = renderHook(() => useCreateSlot(), {
      wrapper: createWrapper(),
    });

    result.current.mutate(payload);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(createSlot).toHaveBeenCalledWith(payload);
  });
});
