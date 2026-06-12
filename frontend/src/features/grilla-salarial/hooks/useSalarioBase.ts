import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as salarioBaseService from '../services/grillaSalarialService';
import type { SalarioBaseCreate, SalarioBaseUpdate } from '../types';

const QUERY_KEY = ['salarios', 'base'] as const;

export function useSalarioBaseList() {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: salarioBaseService.listSalarioBase,
  });
}

export function useSalarioBaseCreate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SalarioBaseCreate) => salarioBaseService.createSalarioBase(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function useSalarioBaseUpdate(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SalarioBaseUpdate) => salarioBaseService.updateSalarioBase(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}
