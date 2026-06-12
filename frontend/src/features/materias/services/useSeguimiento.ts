import { useQuery } from '@tanstack/react-query';
import api from '@/shared/services/api';
import type { SeguimientoItem, SeguimientoFilters } from '../types';

export function useSeguimiento(materiaId: string, filters: SeguimientoFilters = {}) {
  const params = new URLSearchParams();
  if (filters.busqueda) params.set('busqueda', filters.busqueda);
  if (filters.comision) params.set('comision', filters.comision);
  if (filters.actividad) params.set('actividad', filters.actividad);
  if (filters.regional) params.set('regional', filters.regional);
  if (filters.minimo_actividades !== undefined) {
    params.set('minimo_actividades', String(filters.minimo_actividades));
  }
  const queryString = params.toString();

  return useQuery({
    queryKey: ['materia', materiaId, 'seguimiento', filters],
    queryFn: async () => {
      const { data } = await api.get<SeguimientoItem[]>(
        `/materias/${materiaId}/seguimiento${queryString ? `?${queryString}` : ''}`,
      );
      return data;
    },
    staleTime: 1 * 60 * 1000,
  });
}
