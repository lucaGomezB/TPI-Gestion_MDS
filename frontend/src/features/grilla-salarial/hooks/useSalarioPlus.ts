import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as salarioPlusService from '../services/grillaSalarialService';
import type { SalarioPlusCreate, SalarioPlusUpdate } from '../types';

const QUERY_KEY = ['salarios', 'plus'] as const;

export function useSalarioPlusList() {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: salarioPlusService.listSalarioPlus,
  });
}

export function useSalarioPlusCreate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SalarioPlusCreate) => salarioPlusService.createSalarioPlus(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function useSalarioPlusUpdate(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SalarioPlusUpdate) => salarioPlusService.updateSalarioPlus(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}
