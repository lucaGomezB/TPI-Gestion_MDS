// ─── Comunicaciones (envío masivo) ───

export type EstadoComunicacion =
  | 'Pendiente'
  | 'Enviando'
  | 'Enviado'
  | 'Fallido'
  | 'Cancelado';

export interface Comunicacion {
  id: string;
  materia_id: string;
  asunto: string;
  cuerpo: string;
  estado: EstadoComunicacion;
  requiere_aprobacion: boolean;
  aprobado_por?: string | null;
  rechazado_por?: string | null;
  motivo_rechazo?: string | null;
  destinatarios_count: number;
  enviados_count: number;
  fallidos_count: number;
  creado_por: string;
  created_at: string;
  updated_at: string;
}

export interface ComunicacionPreviewRequest {
  asunto: string;
  cuerpo: string;
  materia_id: string;
}

export interface ComunicacionPreviewResponse {
  asunto_renderizado: string;
  cuerpo_renderizado: string;
  destinatarios_ejemplo: Array<{
    nombre: string;
    email: string;
  }>;
  total_destinatarios: number;
}

export interface ComunicacionEnviarRequest {
  asunto: string;
  cuerpo: string;
  materia_id: string;
  requiere_aprobacion?: boolean;
}

export interface AprobarComunicacionRequest {
  accion: 'aprobar' | 'rechazar';
  motivo_rechazo?: string;
}

// ─── Avisos (tablón) ───

export type AlcanceAviso = 'Global' | 'PorMateria' | 'PorCohorte' | 'PorRol';
export type SeveridadAviso = 'Info' | 'Advertencia' | 'Critico';

export interface Aviso {
  id: string;
  titulo: string;
  contenido: string;
  alcance: AlcanceAviso;
  contexto_id?: string | null;
  roles_destino?: string[] | null;
  severidad: SeveridadAviso;
  inicio_vigencia: string;
  fin_vigencia: string;
  requiere_acuse: boolean;
  activo: boolean;
  created_at: string;
  updated_at: string;
}

export interface AvisoFormData {
  titulo: string;
  contenido: string;
  alcance: AlcanceAviso;
  contexto_id?: string;
  roles_destino?: string[];
  severidad: SeveridadAviso;
  inicio_vigencia: string;
  fin_vigencia: string;
  requiere_acuse: boolean;
}

export interface AcknowledgmentAviso {
  id: string;
  aviso_id: string;
  usuario_id: string;
  created_at: string;
}

// ─── Mensajería interna ───

export interface HiloMensaje {
  hilo_id: string;
  asunto: string;
  ultimo_mensaje: string;
  ultima_fecha: string;
  remitente_nombre: string;
  no_leidos: number;
}

export interface Mensaje {
  id: string;
  hilo_id: string;
  remitente_id: string;
  destinatario_id: string;
  asunto: string;
  cuerpo: string;
  leido: boolean;
  created_at: string;
}

export interface MensajeRequest {
  receptor_id: string;
  asunto: string;
  contenido: string;
}

export interface ResponderMensajeRequest {
  contenido: string;
}
