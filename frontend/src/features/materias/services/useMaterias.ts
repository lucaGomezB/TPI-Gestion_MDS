import { useQuery } from '@tanstack/react-query';
import api from '@/shared/services/api';
import type { Materia } from '../types';

async function fetchMaterias(): Promise<Materia[]> {
  const { data } = await api.get<Materia[]>('/materias');
  return data;
}

export function useMaterias() {
  return useQuery({
    queryKey: ['materias'],
    queryFn: fetchMaterias,
    staleTime: 5 * 60 * 1000,
  });
}

export function useMateria(id: string) {
  return useQuery({
    queryKey: ['materia', id],
    queryFn: async () => {
      const { data } = await api.get<Materia>(`/materias/${id}`);
      return data;
    },
    staleTime: 5 * 60 * 1000,
  });
}
