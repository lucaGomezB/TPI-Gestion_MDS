import { useQuery } from '@tanstack/react-query';
import { auditoriaService } from '../services/auditoriaService';

export function useDocenteInteracciones(docenteId: string | undefined) {
  const query = useQuery({
    queryKey: ['auditoria', 'docente-interacciones', docenteId],
    queryFn: () => auditoriaService.getDocenteInteracciones(docenteId!),
    enabled: Boolean(docenteId),
  });

  return {
    data: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
