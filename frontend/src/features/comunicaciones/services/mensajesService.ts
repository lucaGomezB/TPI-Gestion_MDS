import api from '@/shared/services/api';
import type { HiloMensaje, Mensaje, MensajeRequest, ResponderMensajeRequest } from '../types';

export async function getHilosMensajes(): Promise<HiloMensaje[]> {
  const response = await api.get<HiloMensaje[]>('/mensajes');
  return response.data;
}

export async function getHiloMensaje(id: string): Promise<Mensaje[]> {
  const response = await api.get<Mensaje[]>(`/mensajes/${id}`);
  return response.data;
}

export async function enviarMensaje(data: MensajeRequest): Promise<Mensaje> {
  const response = await api.post<Mensaje>('/mensajes', data);
  return response.data;
}

export async function responderMensaje(
  hiloId: string,
  data: ResponderMensajeRequest,
): Promise<Mensaje> {
  const response = await api.post<Mensaje>(`/mensajes/${hiloId}/responder`, data);
  return response.data;
}
