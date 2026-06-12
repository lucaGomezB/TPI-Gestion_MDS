import { useQuery } from '@tanstack/react-query';
import { getConvocatorias } from '../services/coloquioService';

export function useConvocatorias(materiaId?: string) {
  return useQuery({
    queryKey: ['coloquios', 'convocatorias', materiaId],
    queryFn: () => getConvocatorias(materiaId ? { materia_id: materiaId } : undefined),
  });
}
