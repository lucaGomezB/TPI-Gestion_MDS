import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as estructuraService from '../services/estructuraService';
import type { CreateCohorteData, UpdateCohorteData } from '../types/estructura';

export function useCohortes(carreraId?: string) {
  return useQuery({
    queryKey: ['cohortes', { carreraId }],
    queryFn: () => estructuraService.getCohortes(carreraId ? { carrera_id: carreraId } : undefined),
  });
}

export function useCohorte(id: string) {
  return useQuery({
    queryKey: ['cohortes', id],
    queryFn: () => estructuraService.getCohorte(id),
    enabled: !!id,
  });
}

export function useCreateCohorte() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateCohorteData) => estructuraService.createCohorte(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cohortes'] });
    },
  });
}

export function useUpdateCohorte() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateCohorteData }) =>
      estructuraService.updateCohorte(id, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['cohortes'] });
      queryClient.invalidateQueries({ queryKey: ['cohortes', variables.id] });
    },
  });
}
