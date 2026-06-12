import { describe, it, expect } from 'vitest';
import type {
  Materia,
  Calificacion,
  UmbralMateria,
  Atrasado,
  RankingItem,
  Reporte,
  NotaFinal,
  SeguimientoItem,
  ImportPreview,
  ImportActivity,
  AtrasadosFilters,
  SeguimientoFilters,
  MateriaKPI,
  PadronAlumno,
  PadronImportResult,
  CompletionReportItem,
  CompletionReportResult,
  MonitorGeneralItem,
  MonitorGeneralFilters,
} from '@/features/materias/types';

describe('Materias types', () => {
  describe('Materia', () => {
    it('accepts a valid materia object', () => {
      const m: Materia = { id: '1', nombre: 'Matematica', cohorte: '2026', comisiones: ['A', 'B'], tenant_id: 't1' };
      expect(m.id).toBe('1');
      expect(m.nombre).toBe('Matematica');
    });
  });

  describe('Calificacion', () => {
    it('accepts a valid calificacion object', () => {
      const c: Calificacion = {
        id: '1', alumno_id: 'a1', nombre: 'Juan', apellidos: 'Perez',
        email: 'j@t.com', comision: 'A', actividad: 'TP1', nota: 8, fecha: '2026-03-01', tipo: 'tp',
      };
      expect(c.nota).toBe(8);
      expect(c.tipo).toBe('tp');
    });
  });

  describe('UmbralMateria', () => {
    it('accepts a valid umbral object', () => {
      const u: UmbralMateria = { umbral_pct: 60, materia_id: 'm1' };
      expect(u.umbral_pct).toBe(60);
    });
  });

  describe('Atrasado', () => {
    it('accepts a valid atrasado with razon faltante', () => {
      const a: Atrasado = {
        id: '1', alumno_id: 'a1', nombre: 'Juan', apellidos: 'Perez',
        email: 'j@t.com', comision: 'A', razon: 'faltante', umbral: 60,
      };
      expect(a.razon).toBe('faltante');
    });

    it('accepts razon nota_baja with nota_minima', () => {
      const a: Atrasado = {
        id: '2', alumno_id: 'a2', nombre: 'Maria', apellidos: 'Gomez',
        email: 'm@t.com', comision: 'B', razon: 'nota_baja', nota_minima: 3, umbral: 60,
      };
      expect(a.razon).toBe('nota_baja');
      expect(a.nota_minima).toBe(3);
    });
  });

  describe('RankingItem', () => {
    it('accepts a valid ranking item', () => {
      const r: RankingItem = {
        alumno_id: 'a1', nombre: 'Juan', apellidos: 'Perez', comision: 'A',
        actividades_aprobadas: 5, total_actividades: 10, porcentaje: 50,
      };
      expect(r.porcentaje).toBe(50);
    });
  });

  describe('Reporte', () => {
    it('accepts a valid reporte', () => {
      const r: Reporte = {
        total_alumnos: 30, total_actividades: 10, promedio_general: 7.5,
        aprobados: 20, reprobados: 10, atrasados: 5,
      };
      expect(r.total_alumnos).toBe(30);
    });
  });

  describe('NotaFinal', () => {
    it('accepts approved state', () => {
      const n: NotaFinal = {
        alumno_id: 'a1', nombre: 'Juan', apellidos: 'Perez', comision: 'A',
        total_actividades: 10, nota_final: 8, estado: 'aprobado',
      };
      expect(n.estado).toBe('aprobado');
    });

    it('accepts reprobado state', () => {
      const n: NotaFinal = {
        alumno_id: 'a2', nombre: 'Maria', apellidos: 'Lopez', comision: 'B',
        total_actividades: 10, nota_final: 2, estado: 'reprobado',
      };
      expect(n.estado).toBe('reprobado');
    });
  });

  describe('SeguimientoItem', () => {
    it('accepts a valid seguimiento item with optional fields', () => {
      const s: SeguimientoItem = {
        alumno_id: 'a1', nombre: 'Juan', apellidos: 'Perez', email: 'j@t.com',
        comision: 'A', total_actividades: 10, total_aprobadas: 7, total_pendientes: 3,
      };
      expect(s.ultima_actividad).toBeUndefined();
    });

    it('accepts seguimiento with ultima_actividad', () => {
      const s: SeguimientoItem = {
        alumno_id: 'a1', nombre: 'Juan', apellidos: 'Perez', email: 'j@t.com',
        comision: 'A', total_actividades: 10, total_aprobadas: 7, total_pendientes: 3,
        ultima_actividad: 'TP3',
      };
      expect(s.ultima_actividad).toBe('TP3');
    });
  });

  describe('ImportActivity and ImportPreview', () => {
    it('accepts valid import activity', () => {
      const a: ImportActivity = { actividad: 'TP1', filas: 30, seleccionada: true };
      expect(a.seleccionada).toBe(true);
    });

    it('accepts valid import preview', () => {
      const p: ImportPreview = {
        actividades: [{ actividad: 'TP1', filas: 30, seleccionada: true }],
        total_filas: 30,
      };
      expect(p.total_filas).toBe(30);
    });
  });

  describe('AtrasadosFilters', () => {
    it('accepts empty filters', () => {
      const f: AtrasadosFilters = {};
      expect(f.comision).toBeUndefined();
    });

    it('accepts partial filters', () => {
      const f: AtrasadosFilters = { comision: 'A', busqueda: 'Juan' };
      expect(f.comision).toBe('A');
      expect(f.fecha_desde).toBeUndefined();
    });
  });

  describe('SeguimientoFilters', () => {
    it('accepts full filters', () => {
      const f: SeguimientoFilters = {
        busqueda: 'Juan', comision: 'A', actividad: 'TP1', regional: 'CABA', minimo_actividades: 3,
      };
      expect(f.minimo_actividades).toBe(3);
    });
  });

  describe('MateriaKPI', () => {
    it('accepts valid kpi with proximo_examen', () => {
      const materia: Materia = { id: '1', nombre: 'M1', cohorte: '2026', comisiones: ['A'], tenant_id: 't1' };
      const kpi: MateriaKPI = {
        materia, atrasados_count: 5, pendientes_count: 3, proximo_examen: '2026-06-15',
      };
      expect(kpi.proximo_examen).toBe('2026-06-15');
    });

    it('accepts kpi with error', () => {
      const materia: Materia = { id: '1', nombre: 'M1', cohorte: '2026', comisiones: ['A'], tenant_id: 't1' };
      const kpi: MateriaKPI = { materia, atrasados_count: 0, pendientes_count: 0, error: 'Error de carga' };
      expect(kpi.error).toBe('Error de carga');
    });
  });

  describe('PadronAlumno', () => {
    it('accepts a valid padron alumno', () => {
      const p: PadronAlumno = {
        alumno_id: 'a1', nombre: 'Juan', apellidos: 'Perez', email: 'j@t.com', comision: 'A',
      };
      expect(p.alumno_id).toBe('a1');
    });
  });

  describe('PadronImportResult', () => {
    it('accepts a valid import result', () => {
      const r: PadronImportResult = { total_filas: 100, importadas: 95, duplicadas: 5, errores: ['Fila 10: DNI duplicado'] };
      expect(r.importadas).toBe(95);
      expect(r.errores.length).toBe(1);
    });

    it('accepts result without errors', () => {
      const r: PadronImportResult = { total_filas: 50, importadas: 50, duplicadas: 0, errores: [] };
      expect(r.duplicadas).toBe(0);
    });
  });

  describe('CompletionReportItem', () => {
    it('accepts completed item', () => {
      const item: CompletionReportItem = {
        alumno_id: 'a1', nombre: 'Juan', apellidos: 'Perez', email: 'j@t.com',
        actividad: 'TP1', estado: 'completado', fecha_entrega: '2026-03-01',
      };
      expect(item.estado).toBe('completado');
    });

    it('accepts pending item without date', () => {
      const item: CompletionReportItem = {
        alumno_id: 'a2', nombre: 'Maria', apellidos: 'Lopez', email: 'm@t.com',
        actividad: 'TP1', estado: 'pendiente',
      };
      expect(item.estado).toBe('pendiente');
      expect(item.fecha_entrega).toBeUndefined();
    });
  });

  describe('CompletionReportResult', () => {
    it('accepts valid result', () => {
      const r: CompletionReportResult = {
        materia_id: 'm1', total_alumnos: 30, total_pendientes: 5, total_completados: 25,
        items: [
          { alumno_id: 'a1', nombre: 'J', apellidos: 'P', email: 'j@t.com', actividad: 'TP1', estado: 'pendiente' },
        ],
      };
      expect(r.total_pendientes).toBe(5);
    });
  });

  describe('MonitorGeneralItem', () => {
    it('accepts a valid monitor item', () => {
      const item: MonitorGeneralItem = {
        materia_id: 'm1', materia_nombre: 'Matematica', cohorte: '2026', comision: 'A',
        total_alumnos: 30, total_actividades: 10, promedio_general: 7.5,
        aprobados: 20, reprobados: 10, atrasados_count: 3, pendientes_count: 2,
      };
      expect(item.materia_nombre).toBe('Matematica');
    });
  });

  describe('MonitorGeneralFilters', () => {
    it('accepts empty filters', () => {
      const f: MonitorGeneralFilters = {};
      expect(f.materia_id).toBeUndefined();
    });

    it('accepts status filter', () => {
      const f: MonitorGeneralFilters = { status: 'con_atrasados' };
      expect(f.status).toBe('con_atrasados');
    });

    it('accepts all filters', () => {
      const f: MonitorGeneralFilters = {
        materia_id: 'm1', regional: 'CABA', comision: 'A', busqueda: 'Mate', status: 'todos',
      };
      expect(f.busqueda).toBe('Mate');
    });
  });
});
