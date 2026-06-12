import { useMutation, useQueryClient } from '@tanstack/react-query';
import { reservarTurno } from '../services/coloquioService';
import type { ReservarTurnoPayload } from '../types/coloquioTypes';

export function useReservarTurno(coloquioId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ReservarTurnoPayload) => reservarTurno(coloquioId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coloquios', 'agenda', coloquioId] });
    },
  });
}
