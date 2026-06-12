import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createSlot } from '../services/encuentroService';
import type { CreateSlotPayload } from '../types/encuentroTypes';

export function useCreateSlot() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateSlotPayload) => createSlot(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['encuentros'] });
    },
  });
}
