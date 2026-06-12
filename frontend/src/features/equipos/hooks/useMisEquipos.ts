import { useQuery } from '@tanstack/react-query';
import * as asignacionesService from '../services/asignacionesService';

export function useMisEquipos() {
  return useQuery({
    queryKey: ['mis-equipos'],
    queryFn: asignacionesService.getMisEquipos,
  });
}
