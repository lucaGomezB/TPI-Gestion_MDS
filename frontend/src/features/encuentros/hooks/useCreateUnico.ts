import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createUnico } from '../services/encuentroService';
import type { CreateUnicoPayload } from '../types/encuentroTypes';

export function useCreateUnico() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateUnicoPayload) => createUnico(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['encuentros'] });
    },
  });
}
