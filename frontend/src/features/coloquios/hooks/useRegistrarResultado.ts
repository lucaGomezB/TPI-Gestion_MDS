import { useMutation, useQueryClient } from '@tanstack/react-query';
import { registrarResultado } from '../services/coloquioService';
import type { RegistrarResultadoPayload } from '../types/coloquioTypes';

export function useRegistrarResultado(coloquioId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: RegistrarResultadoPayload) => registrarResultado(coloquioId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coloquios', 'agenda', coloquioId] });
      queryClient.invalidateQueries({ queryKey: ['coloquios', 'resultados', coloquioId] });
    },
  });
}
