import { useQuery } from '@tanstack/react-query';
import { getEncuentrosAdmin } from '../services/encuentroService';
import type { AdminEncuentrosQueryParams } from '../types/encuentroTypes';

export function useEncuentros(params: Partial<AdminEncuentrosQueryParams> = {}) {
  return useQuery({
    queryKey: ['encuentros', 'admin', params],
    queryFn: () => getEncuentrosAdmin(params),
  });
}

export function useEncuentro(id: string | undefined) {
  return useQuery({
    queryKey: ['encuentros', id],
    queryFn: () => getEncuentrosAdmin({ page: 1, per_page: 1 }).then(() => null),
    enabled: false,
  });
}
