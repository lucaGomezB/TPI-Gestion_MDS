import { useQuery } from '@tanstack/react-query';
import { getAgenda } from '../services/coloquioService';

export function useAgenda(coloquioId: string) {
  return useQuery({
    queryKey: ['coloquios', 'agenda', coloquioId],
    queryFn: () => getAgenda(coloquioId),
    enabled: !!coloquioId,
  });
}
