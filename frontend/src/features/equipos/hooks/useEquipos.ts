import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as docentesService from '../services/docentesService';
import type { CreateDocenteData, UpdateDocenteData } from '../types/docentes';

export function useDocentes() {
  return useQuery({
    queryKey: ['docentes'],
    queryFn: docentesService.getDocentes,
  });
}

export function useDocente(id: string) {
  return useQuery({
    queryKey: ['docentes', id],
    queryFn: () => docentesService.getDocente(id),
    enabled: !!id,
  });
}

export function useCreateDocente() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateDocenteData) => docentesService.createDocente(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['docentes'] });
    },
  });
}

export function useUpdateDocente() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateDocenteData }) =>
      docentesService.updateDocente(id, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['docentes'] });
      queryClient.invalidateQueries({ queryKey: ['docentes', variables.id] });
    },
  });
}
