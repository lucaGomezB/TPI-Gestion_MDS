import api from '../../../shared/services/api';
import type {
  AuditFilters,
  AuditSearchResponse,
  DocenteInteracciones,
  AccionesPorDia,
} from '../types';

export const auditoriaService = {
  async search(filters: AuditFilters): Promise<AuditSearchResponse> {
    const params = new URLSearchParams();
    if (filters.q) params.set('q', filters.q);
    if (filters.accion) params.set('accion', filters.accion);
    if (filters.actor_id) params.set('actor_id', filters.actor_id);
    if (filters.materia_id) params.set('materia_id', filters.materia_id);
    if (filters.ip) params.set('ip', filters.ip);
    if (filters.fecha_desde) params.set('fecha_desde', filters.fecha_desde);
    if (filters.fecha_hasta) params.set('fecha_hasta', filters.fecha_hasta);
    params.set('limit', String(filters.limit));
    params.set('offset', String(filters.offset));

    const response = await api.get<AuditSearchResponse>(
      `/admin/auditoria?${params.toString()}`,
    );
    return response.data;
  },

  async getDocenteInteracciones(
    docenteId: string,
  ): Promise<DocenteInteracciones> {
    const response = await api.get<DocenteInteracciones>(
      `/admin/auditoria/docentes/${docenteId}/interacciones`,
    );
    return response.data;
  },

  exportUrl(filters: AuditFilters, formato: 'csv' | 'json'): string {
    const params = new URLSearchParams();
    if (filters.q) params.set('q', filters.q);
    if (filters.accion) params.set('accion', filters.accion);
    if (filters.actor_id) params.set('actor_id', filters.actor_id);
    if (filters.materia_id) params.set('materia_id', filters.materia_id);
    if (filters.ip) params.set('ip', filters.ip);
    if (filters.fecha_desde) params.set('fecha_desde', filters.fecha_desde);
    if (filters.fecha_hasta) params.set('fecha_hasta', filters.fecha_hasta);
    params.set('formato', formato);
    return `/api/admin/auditoria/exportar?${params.toString()}`;
  },

  async getAccionesPorDia(
    fecha_desde: string,
    fecha_hasta: string,
  ): Promise<AccionesPorDia[]> {
    const params = new URLSearchParams();
    params.set('fecha_desde', fecha_desde);
    params.set('fecha_hasta', fecha_hasta);
    const response = await api.get<AccionesPorDia[]>(
      `/admin/auditoria/acciones-por-dia?${params.toString()}`,
    );
    return response.data;
  },
};
