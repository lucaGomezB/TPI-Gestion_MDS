import { useQuery } from '@tanstack/react-query';
import api from '@/shared/services/api';
import type { Reporte, NotaFinal } from '../types';

export function useReportes(materiaId: string) {
  return useQuery({
    queryKey: ['materia', materiaId, 'reportes'],
    queryFn: async () => {
      const { data } = await api.get<Reporte>(`/materias/${materiaId}/reportes`);
      return data;
    },
    staleTime: 1 * 60 * 1000,
  });
}

export function useNotasFinales(materiaId: string) {
  return useQuery({
    queryKey: ['materia', materiaId, 'notas-finales'],
    queryFn: async () => {
      const { data } = await api.get<NotaFinal[]>(`/materias/${materiaId}/notas-finales`);
      return data;
    },
    staleTime: 1 * 60 * 1000,
  });
}

function getDateStamp(): string {
  return new Date().toISOString().slice(0, 10);
}

export function useExportNotasFinales() {
  return async (materiaId: string) => {
    const response = await api.get(`/materias/${materiaId}/notas-finales`, {
      params: { exportar: 'csv' },
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `notas-finales-${materiaId}-${getDateStamp()}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };
}

export function useExportAtrasados() {
  return async (materiaId: string) => {
    const response = await api.get(`/materias/${materiaId}/export/atrasados`, {
      params: { exportar: 'csv' },
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `atrasados-${materiaId}-${getDateStamp()}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };
}
