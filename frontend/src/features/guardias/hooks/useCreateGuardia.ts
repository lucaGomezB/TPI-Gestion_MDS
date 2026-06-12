import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createGuardia } from '../services/guardiaService';
import type { CreateGuardiaPayload } from '../types/guardiaTypes';

export function useCreateGuardia(materiaId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateGuardiaPayload) => createGuardia(materiaId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guardias', materiaId] });
    },
  });
}
