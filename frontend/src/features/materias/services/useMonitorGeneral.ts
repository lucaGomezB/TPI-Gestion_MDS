import { useQuery } from '@tanstack/react-query';
import api from '@/shared/services/api';
import type { MonitorGeneralItem, MonitorGeneralFilters } from '../types';

export function useMonitorGeneral(filters: MonitorGeneralFilters = {}) {
  const params = new URLSearchParams();
  if (filters.materia_id) params.set('materia_id', filters.materia_id);
  if (filters.regional) params.set('regional', filters.regional);
  if (filters.comision) params.set('comision', filters.comision);
  if (filters.busqueda) params.set('busqueda', filters.busqueda);
  if (filters.status && filters.status !== 'todos') params.set('status', filters.status);
  const queryString = params.toString();

  return useQuery({
    queryKey: ['materias', 'monitor-general', filters],
    queryFn: async () => {
      const { data } = await api.get<{ items: MonitorGeneralItem[]; total: number }>(
        `/admin/materias/monitor-general${queryString ? `?${queryString}` : ''}`,
      );
      return data.items || [];
    },
    staleTime: 1 * 60 * 1000,
  });
}

export function useExportMonitorGeneral() {
  return async (filters: MonitorGeneralFilters = {}) => {
    const params = new URLSearchParams();
    if (filters.materia_id) params.set('materia_id', filters.materia_id);
    if (filters.regional) params.set('regional', filters.regional);
    if (filters.comision) params.set('comision', filters.comision);
    if (filters.busqueda) params.set('busqueda', filters.busqueda);
    if (filters.status && filters.status !== 'todos') params.set('status', filters.status);
    const queryString = params.toString();

    const response = await api.get(
      `/admin/materias/monitor-general/export${queryString ? `?${queryString}` : ''}`,
      { responseType: 'blob' },
    );
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    const now = new Date().toISOString().slice(0, 10);
    link.setAttribute('download', `monitor-general-${now}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };
}
