import { useQuery } from '@tanstack/react-query';
import { auditoriaService } from '../services/auditoriaService';
import type { AccionesPorDia } from '../types';

interface AuditDashboardResult {
  acciones_por_dia: AccionesPorDia[];
  total_acciones: number;
  total_dias: number;
}

export function useAuditDashboard(
  fecha_desde: string,
  fecha_hasta: string,
) {
  const query = useQuery({
    queryKey: ['auditoria', 'dashboard', fecha_desde, fecha_hasta],
    queryFn: async (): Promise<AuditDashboardResult> => {
      const data = await auditoriaService.getAccionesPorDia(
        fecha_desde,
        fecha_hasta,
      );
      const total_acciones = data.reduce((sum, d) => sum + d.total, 0);
      const total_dias = data.length;
      return { acciones_por_dia: data, total_acciones, total_dias };
    },
    enabled: Boolean(fecha_desde && fecha_hasta),
  });

  return {
    data: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
