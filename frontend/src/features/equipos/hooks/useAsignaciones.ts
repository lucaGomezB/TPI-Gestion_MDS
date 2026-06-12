import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as asignacionesService from '../services/asignacionesService';
import type {
  AsignacionFilters,
  CreateAsignacionData,
  UpdateAsignacionData,
} from '../types/asignaciones';

export function useAsignaciones(filters?: AsignacionFilters) {
  return useQuery({
    queryKey: ['asignaciones', { ...filters }],
    queryFn: () => asignacionesService.getAsignaciones(filters),
  });
}

export function useAsignacion(id: string) {
  return useQuery({
    queryKey: ['asignaciones', id],
    queryFn: () => asignacionesService.getAsignacion(id),
    enabled: !!id,
  });
}

export function useCreateAsignacion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateAsignacionData) => asignacionesService.createAsignacion(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['asignaciones'] });
    },
  });
}

export function useUpdateAsignacion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateAsignacionData }) =>
      asignacionesService.updateAsignacion(id, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['asignaciones'] });
      queryClient.invalidateQueries({ queryKey: ['asignaciones', variables.id] });
    },
  });
}
