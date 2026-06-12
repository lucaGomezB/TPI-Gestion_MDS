import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as estructuraService from '../services/estructuraService';
import type { CreateCarreraData, UpdateCarreraData } from '../types/estructura';

export function useCarreras() {
  return useQuery({
    queryKey: ['carreras'],
    queryFn: estructuraService.getCarreras,
  });
}

export function useCarrera(id: string) {
  return useQuery({
    queryKey: ['carreras', id],
    queryFn: () => estructuraService.getCarrera(id),
    enabled: !!id,
  });
}

export function useCreateCarrera() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateCarreraData) => estructuraService.createCarrera(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['carreras'] });
    },
  });
}

export function useUpdateCarrera() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateCarreraData }) =>
      estructuraService.updateCarrera(id, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['carreras'] });
      queryClient.invalidateQueries({ queryKey: ['carreras', variables.id] });
    },
  });
}
