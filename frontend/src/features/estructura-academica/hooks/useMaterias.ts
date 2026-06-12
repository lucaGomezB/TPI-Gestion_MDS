import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as estructuraService from '../services/estructuraService';
import type { CreateMateriaData, UpdateMateriaData } from '../types/estructura';

export function useMaterias() {
  return useQuery({
    queryKey: ['materias'],
    queryFn: estructuraService.getMaterias,
  });
}

export function useMateria(id: string) {
  return useQuery({
    queryKey: ['materias', id],
    queryFn: () => estructuraService.getMateria(id),
    enabled: !!id,
  });
}

export function useCreateMateria() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateMateriaData) => estructuraService.createMateria(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materias'] });
    },
  });
}

export function useUpdateMateria() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateMateriaData }) =>
      estructuraService.updateMateria(id, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['materias'] });
      queryClient.invalidateQueries({ queryKey: ['materias', variables.id] });
    },
  });
}

export function useUploadPrograma() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      materiaId,
      carreraId,
      cohorteId,
      titulo,
      file,
    }: {
      materiaId: string;
      carreraId: string;
      cohorteId: string;
      titulo: string;
      file: File;
    }) => estructuraService.uploadPrograma(materiaId, carreraId, cohorteId, titulo, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['programas'] });
    },
  });
}

export function useProgramas(materiaId: string) {
  return useQuery({
    queryKey: ['programas', { materiaId }],
    queryFn: () => estructuraService.getProgramas(materiaId),
    enabled: !!materiaId,
  });
}
