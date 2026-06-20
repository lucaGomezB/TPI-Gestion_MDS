import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getComunicaciones,
  previewComunicacion,
  enviarComunicacion,
  aprobarComunicacion,
  cancelarComunicacion,
} from '../services/comunicacionesService';
import type {
  ComunicacionPreviewRequest,
  ComunicacionEnviarRequest,
  AprobarComunicacionRequest,
} from '../types';

const COMUNICACIONES_KEY = ['comunicaciones'] as const;

/** materiaId is REQUIRED — backend endpoint is /materias/{id}/comunicaciones. */
export function useComunicaciones(materiaId: string) {
  return useQuery({
    queryKey: [...COMUNICACIONES_KEY, materiaId],
    queryFn: () => getComunicaciones(materiaId),
    enabled: !!materiaId,
  });
}

export function usePreviewComunicacion() {
  return useMutation({
    mutationFn: ({
      materiaId,
      data,
    }: {
      materiaId: string;
      data: ComunicacionPreviewRequest;
    }) => previewComunicacion(materiaId, data),
  });
}

export function useEnviarComunicacion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      materiaId,
      data,
    }: {
      materiaId: string;
      data: ComunicacionEnviarRequest;
    }) => enviarComunicacion(materiaId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: COMUNICACIONES_KEY });
    },
  });
}

export function useAprobarComunicacion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AprobarComunicacionRequest }) =>
      aprobarComunicacion(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: COMUNICACIONES_KEY });
    },
  });
}

export function useCancelarComunicacion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => cancelarComunicacion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: COMUNICACIONES_KEY });
    },
  });
}
