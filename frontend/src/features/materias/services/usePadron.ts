import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/shared/services/api';
import type { PadronImportResult } from '../types';

export function useUploadPadron(materiaId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (file: File): Promise<PadronImportResult> => {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await api.post<PadronImportResult>(
        `/materias/${materiaId}/padron`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } },
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materia', materiaId, 'atrasados'] });
      queryClient.invalidateQueries({ queryKey: ['materia', materiaId, 'reportes'] });
    },
  });
}

export function useReplacePadron(materiaId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (file: File): Promise<PadronImportResult> => {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await api.put<PadronImportResult>(
        `/materias/${materiaId}/padron`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } },
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materia', materiaId, 'atrasados'] });
      queryClient.invalidateQueries({ queryKey: ['materia', materiaId, 'reportes'] });
    },
  });
}
