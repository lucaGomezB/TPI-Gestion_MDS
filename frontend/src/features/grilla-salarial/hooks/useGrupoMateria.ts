import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as grupoService from '../services/grillaSalarialService';
import type { GrupoMateriaCreate, GrupoMateriaUpdate, MateriasAsignarRequest } from '../types';

const LIST_KEY = ['salarios', 'grupos'] as const;

export function useGrupoMateriaList() {
  return useQuery({
    queryKey: LIST_KEY,
    queryFn: grupoService.listGruposMateria,
  });
}

export function useGrupoMateriaCreate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: GrupoMateriaCreate) => grupoService.createGrupoMateria(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: LIST_KEY });
    },
  });
}

export function useGrupoMateriaUpdate(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: GrupoMateriaUpdate) => grupoService.updateGrupoMateria(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: LIST_KEY });
    },
  });
}

export function useMateriasByGrupo(grupoId: string) {
  return useQuery({
    queryKey: ['salarios', 'grupos', grupoId, 'materias'],
    queryFn: () => grupoService.getMateriasByGrupo(grupoId),
    enabled: !!grupoId,
  });
}

export function useAssignMaterias(grupoId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: MateriasAsignarRequest) => grupoService.assignMateriasToGrupo(grupoId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['salarios', 'grupos', grupoId, 'materias'] });
    },
  });
}
