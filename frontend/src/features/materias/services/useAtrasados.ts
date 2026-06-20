import { useQuery } from '@tanstack/react-query';
import api from '@/shared/services/api';
import type { Atrasado, AtrasadosFilters, RankingItem } from '../types';

export function useAtrasados(materiaId: string, filters: AtrasadosFilters = {}) {
  const params = new URLSearchParams();
  if (filters.comision) params.set('comision', filters.comision);
  if (filters.busqueda) params.set('busqueda', filters.busqueda);
  if (filters.fecha_desde) params.set('fecha_desde', filters.fecha_desde);
  if (filters.fecha_hasta) params.set('fecha_hasta', filters.fecha_hasta);
  const queryString = params.toString();

  return useQuery({
    queryKey: ['materia', materiaId, 'atrasados', filters],
    queryFn: async () => {
      const { data } = await api.get<{ items: Atrasado[]; total: number }>(
        `/materias/${materiaId}/atrasados${queryString ? `?${queryString}` : ''}`,
      );
      return data.items || [];
    },
    staleTime: 1 * 60 * 1000,
  });
}

export function useRanking(materiaId: string) {
  return useQuery({
    queryKey: ['materia', materiaId, 'ranking'],
    queryFn: async () => {
      const { data } = await api.get<{ items: RankingItem[]; total: number }>(
        `/materias/${materiaId}/ranking`,
      );
      return data.items || [];
    },
    staleTime: 1 * 60 * 1000,
  });
}
