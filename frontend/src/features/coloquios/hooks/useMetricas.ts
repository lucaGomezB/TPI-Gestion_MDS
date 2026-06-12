import { useQuery } from '@tanstack/react-query';
import { getMetricas } from '../services/coloquioService';

export function useMetricas() {
  return useQuery({
    queryKey: ['coloquios', 'metricas'],
    queryFn: () => getMetricas(),
  });
}
