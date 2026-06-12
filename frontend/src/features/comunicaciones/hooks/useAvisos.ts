import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getAvisos,
  getAvisosAdmin,
  getAviso,
  createAviso,
  updateAviso,
  deleteAviso,
  acknowledgeAviso,
  getAcknowledgmentStatus,
} from '../services/avisosService';
import type { AvisoFormData } from '../types';

const AVISOS_KEY = ['avisos'] as const;
const AVISOS_ADMIN_KEY = ['avisos', 'admin'] as const;

export function useAvisos() {
  return useQuery({
    queryKey: AVISOS_KEY,
    queryFn: getAvisos,
  });
}

export function useAvisosAdmin() {
  return useQuery({
    queryKey: AVISOS_ADMIN_KEY,
    queryFn: getAvisosAdmin,
  });
}

export function useAviso(id: string) {
  return useQuery({
    queryKey: [...AVISOS_ADMIN_KEY, id],
    queryFn: () => getAviso(id),
    enabled: !!id,
  });
}

export function useCreateAviso() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AvisoFormData) => createAviso(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: AVISOS_ADMIN_KEY });
    },
  });
}

export function useUpdateAviso() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<AvisoFormData> }) =>
      updateAviso(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: AVISOS_ADMIN_KEY });
    },
  });
}

export function useDeleteAviso() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteAviso(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: AVISOS_ADMIN_KEY });
    },
  });
}

export function useAcknowledgeAviso() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (avisoId: string) => acknowledgeAviso(avisoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: AVISOS_KEY });
    },
  });
}

export function useAcknowledgmentStatus(avisoId: string) {
  return useQuery({
    queryKey: [...AVISOS_ADMIN_KEY, avisoId, 'ack-status'],
    queryFn: () => getAcknowledgmentStatus(avisoId),
    enabled: !!avisoId,
  });
}
