import api from '@/shared/services/api';
import type { HiloMensaje, HiloResponse, Mensaje, MensajeRequest, ResponderMensajeRequest } from '../types';

export async function getHilosMensajes(): Promise<HiloMensaje[]> {
  const response = await api.get<{ data: HiloMensaje[] }>('/mensajes');
  return response.data.data ?? [];
}

/** GET /mensajes/{id} — returns HiloResponse, extract the mensajes array. */
export async function getHiloMensaje(id: string): Promise<HiloResponse> {
  const response = await api.get<HiloResponse>(`/mensajes/${id}`);
  return response.data;
}

/** POST /mensajes — backend expects MensajeCreate { destinatario_id, asunto, cuerpo }. */
export async function enviarMensaje(data: MensajeRequest): Promise<Mensaje> {
  const response = await api.post<Mensaje>('/mensajes', data);
  return response.data;
}

/** POST /mensajes/{hiloId}/responder — backend expects MensajeResponder { cuerpo }. */
export async function responderMensaje(
  hiloId: string,
  data: ResponderMensajeRequest,
): Promise<Mensaje> {
  const response = await api.post<Mensaje>(`/mensajes/${hiloId}/responder`, data);
  return response.data;
}
