import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateEncuentro } from '../services/encuentroService';
import type { UpdateEncuentroPayload } from '../types/encuentroTypes';

export function useUpdateEncuentro() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateEncuentroPayload }) =>
      updateEncuentro(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['encuentros'] });
    },
  });
}
