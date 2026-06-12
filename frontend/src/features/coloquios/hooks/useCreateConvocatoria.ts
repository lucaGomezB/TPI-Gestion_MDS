import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createConvocatoria } from '../services/coloquioService';
import type { CreateColoquioPayload } from '../types/coloquioTypes';

export function useCreateConvocatoria() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateColoquioPayload) => createConvocatoria(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coloquios'] });
    },
  });
}
