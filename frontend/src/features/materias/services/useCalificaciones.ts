import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/shared/services/api';
import type { Calificacion, UmbralMateria } from '../types';

export function useCalificaciones(materiaId: string) {
  return useQuery({
    queryKey: ['materia', materiaId, 'calificaciones'],
    queryFn: async () => {
      const { data } = await api.get<{ items: Calificacion[]; total: number }>(
        `/materias/${materiaId}/calificaciones`,
      );
      return data.items || [];
    },
    staleTime: 1 * 60 * 1000,
  });
}

export function useUmbral(materiaId: string) {
  return useQuery({
    queryKey: ['materia', materiaId, 'umbral'],
    queryFn: async () => {
      const { data } = await api.get<UmbralMateria>(`/materias/${materiaId}/calificaciones/umbral`);
      return data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useUpdateUmbral(materiaId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (umbralPct: number) => {
      const { data } = await api.post<UmbralMateria>(`/materias/${materiaId}/calificaciones/umbral`, {
        umbral_pct: umbralPct,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materia', materiaId, 'umbral'] });
    },
  });
}

export function useImportarCalificaciones(materiaId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await api.post(`/materias/${materiaId}/calificaciones/importar`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materia', materiaId, 'calificaciones'] });
      queryClient.invalidateQueries({ queryKey: ['materia', materiaId, 'reportes'] });
    },
  });
}

export function useConfirmImport(materiaId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (actividades: string[]) => {
      const { data } = await api.post(`/materias/${materiaId}/calificaciones/importar/confirmar`, {
        actividades,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materia', materiaId, 'calificaciones'] });
      queryClient.invalidateQueries({ queryKey: ['materia', materiaId, 'reportes'] });
    },
  });
}

export function useVaciarCalificaciones(materiaId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      await api.delete(`/materias/${materiaId}/calificaciones`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materia', materiaId, 'calificaciones'] });
      queryClient.invalidateQueries({ queryKey: ['materia', materiaId, 'reportes'] });
    },
  });
}
