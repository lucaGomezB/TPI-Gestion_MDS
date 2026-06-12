import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as liquidacionService from '../services/liquidacionService';
import type { LiquidacionListParams, HistorialParams } from '../services/liquidacionService';

export function useLiquidacionList(params: LiquidacionListParams) {
  return useQuery({
    queryKey: ['liquidaciones', 'periodo', params],
    queryFn: () => liquidacionService.listLiquidaciones(params),
    enabled: !!params.periodo,
  });
}

export function useLiquidacionDetail(id: string) {
  return useQuery({
    queryKey: ['liquidaciones', id],
    queryFn: () => liquidacionService.getLiquidacionDetail(id),
    enabled: !!id,
  });
}

export function useCerrarLiquidacion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => liquidacionService.cerrarLiquidacion(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: ['liquidaciones'] });
      queryClient.invalidateQueries({ queryKey: ['liquidaciones', id] });
    },
  });
}

export function useHistorial(params: HistorialParams) {
  return useQuery({
    queryKey: ['liquidaciones', 'historial', params],
    queryFn: () => liquidacionService.getHistorial(params),
  });
}
