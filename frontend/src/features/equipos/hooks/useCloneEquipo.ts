import { useMutation } from '@tanstack/react-query';
import * as asignacionesService from '../services/asignacionesService';
import type { CloneEquipoData } from '../types/asignaciones';

export function useCloneEquipo() {
  return useMutation({
    mutationFn: (data: CloneEquipoData) => asignacionesService.cloneEquipo(data),
  });
}
