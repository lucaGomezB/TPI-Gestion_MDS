import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as evaluacionesService from '../services/evaluacionesService';
import type {
  CreateEvaluationDateData,
  UpdateEvaluationDateData,
  EvaluacionesQueryParams,
} from '../types';

// --- Task 3.1: List evaluaciones ---

export function useEvaluaciones(params?: EvaluacionesQueryParams) {
  return useQuery({
    queryKey: ['evaluaciones', { ...params }],
    queryFn: () => evaluacionesService.getEvaluaciones(params),
  });
}

// --- Task 3.2: Create evaluacion ---

export function useCreateEvaluacion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateEvaluationDateData) => evaluacionesService.createEvaluacion(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evaluaciones'] });
    },
  });
}

// --- Task 3.3: Update evaluacion ---

export function useUpdateEvaluacion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateEvaluationDateData }) =>
      evaluacionesService.updateEvaluacion(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evaluaciones'] });
    },
  });
}

// --- Task 3.4: Delete evaluacion ---

export function useDeleteEvaluacion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => evaluacionesService.deleteEvaluacion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evaluaciones'] });
    },
  });
}

// --- Task 3.5: Generate embed ---

export function useGenerateEmbed() {
  return useMutation({
    mutationFn: ({ materia_id, formato }: { materia_id: string; formato?: string }) =>
      evaluacionesService.generateEmbed(materia_id, formato),
  });
}
