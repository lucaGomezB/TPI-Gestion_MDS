import { useQuery } from '@tanstack/react-query';
import { getGuardias } from '../services/guardiaService';
import type { GuardiaFilters } from '../types/guardiaTypes';

export function useGuardias(materiaId: string, filters: Partial<GuardiaFilters> = {}) {
  return useQuery({
    queryKey: ['guardias', materiaId, filters],
    queryFn: () => getGuardias(materiaId, filters),
    enabled: !!materiaId,
  });
}
