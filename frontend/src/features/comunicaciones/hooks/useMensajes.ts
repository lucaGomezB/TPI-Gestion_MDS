import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getHilosMensajes,
  getHiloMensaje,
  enviarMensaje,
  responderMensaje,
} from '../services/mensajesService';
import type { MensajeRequest, ResponderMensajeRequest } from '../types';

const MENSAJES_KEY = ['mensajes'] as const;

export function useHilosMensajes() {
  return useQuery({
    queryKey: MENSAJES_KEY,
    queryFn: getHilosMensajes,
  });
}

export function useHiloMensaje(id: string) {
  return useQuery({
    queryKey: [...MENSAJES_KEY, id],
    queryFn: () => getHiloMensaje(id),
    enabled: !!id,
  });
}

export function useEnviarMensaje() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: MensajeRequest) => enviarMensaje(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MENSAJES_KEY });
    },
  });
}

export function useResponderMensaje() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      hiloId,
      data,
    }: {
      hiloId: string;
      data: ResponderMensajeRequest;
    }) => responderMensaje(hiloId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: MENSAJES_KEY });
      queryClient.invalidateQueries({ queryKey: [...MENSAJES_KEY, variables.hiloId] });
    },
  });
}
