export interface ConvocatoriaColoquio {
  id: string;
  materia_id: string;
  materia_nombre: string;
  titulo: string;
  activa: boolean;
  dias: DiaColoquio[];
  total_convocados: number;
  reservas_activas: number;
  cupos_libres: number;
  created_at: string;
  updated_at: string;
}

export interface DiaColoquio {
  id: string;
  fecha: string;
  cupos: number;
  reservados: number;
  libre: number;
}

export interface ReservaColoquio {
  id: string;
  alumno_id: string;
  alumno_nombre: string;
  alumno_apellido: string;
  confirmada: boolean;
  created_at: string;
}

export interface ResultadoColoquio {
  id: string;
  alumno_id: string;
  alumno_nombre: string;
  alumno_apellido: string;
  nota: number;
  aprobado: boolean;
  registrado_por: string;
  created_at: string;
}

export interface CreateColoquioPayload {
  materia_id: string;
  titulo: string;
  dias: {
    fecha: string;
    cupos: number;
  }[];
}

export interface MetricasColoquio {
  total_convocatorias_activas: number;
  total_alumnos_importados: number;
  total_reservas_activas: number;
  total_resultados_registrados: number;
}

export interface AgendaColoquio {
  convocatoria: {
    id: string;
    materia_nombre: string;
    titulo: string;
    activa: boolean;
  };
  dias: DiaAgenda[];
}

export interface DiaAgenda {
  id: string;
  fecha: string;
  cupos: number;
  reservados: number;
  libre: number;
  reservas: ReservaColoquio[];
}

export interface RegistrarResultadoPayload {
  alumno_id: string;
  nota: number;
  aprobado: boolean;
}

export interface ReservarTurnoPayload {
  dia_id: string;
  alumno_id: string;
}
