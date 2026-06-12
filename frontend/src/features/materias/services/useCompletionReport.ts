import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/shared/services/api';
import type { CompletionReportResult } from '../types';

export function useCompletionReport(materiaId: string) {
  return useQuery({
    queryKey: ['materia', materiaId, 'completion-report'],
    queryFn: async () => {
      const { data } = await api.get<CompletionReportResult>(
        `/materias/${materiaId}/completion-report`,
      );
      return data;
    },
    staleTime: 1 * 60 * 1000,
  });
}

export function useUploadCompletionReport(materiaId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (file: File): Promise<CompletionReportResult> => {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await api.post<CompletionReportResult>(
        `/materias/${materiaId}/completion-report`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } },
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materia', materiaId, 'completion-report'] });
    },
  });
}

export function useExportCompletionReport() {
  return async (materiaId: string) => {
    const response = await api.get(`/materias/${materiaId}/completion-report`, {
      params: { exportar: 'csv' },
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    const now = new Date().toISOString().slice(0, 10);
    link.setAttribute('download', `completion-report-${materiaId}-${now}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };
}
