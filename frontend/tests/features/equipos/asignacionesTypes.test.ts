import { describe, it, expect } from 'vitest';
import {
  createAsignacionSchema,
  cloneEquipoSchema,
  vigenciaBulkSchema,
  exportEquipoSchema,
} from '../../../src/features/equipos/types/asignaciones';

describe('Asignacion Schema Validation', () => {
  const validAsignacion = {
    docente_id: '550e8400-e29b-41d4-a716-446655440000',
    materia_id: '550e8400-e29b-41d4-a716-446655440001',
    carrera_id: '550e8400-e29b-41d4-a716-446655440002',
    cohorte_id: '550e8400-e29b-41d4-a716-446655440003',
    rol: 'PROFESOR',
    comisiones: ['A', 'B'],
    responsable_id: null,
    vig_desde: '2026-01-01',
    vig_hasta: '2026-12-31',
  };

  it('accepts valid asignacion data', () => {
    const result = createAsignacionSchema.safeParse(validAsignacion);
    expect(result.success).toBe(true);
  });

  it('rejects missing docente', () => {
    const data = { ...validAsignacion, docente_id: '' };
    const result = createAsignacionSchema.safeParse(data);
    expect(result.success).toBe(false);
  });

  it('accepts without comisiones (defaults to [])', () => {
    const data = { ...validAsignacion };
    delete data.comisiones;
    const result = createAsignacionSchema.safeParse(data);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.comisiones).toEqual([]);
    }
  });
});

describe('cloneEquipoSchema Validation', () => {
  it('accepts different source and destination', () => {
    const data = {
      source_materia_id: '550e8400-e29b-41d4-a716-446655440001',
      source_carrera_id: '550e8400-e29b-41d4-a716-446655440002',
      source_cohorte_id: '550e8400-e29b-41d4-a716-446655440003',
      dest_materia_id: '550e8400-e29b-41d4-a716-446655440004',
      dest_carrera_id: '550e8400-e29b-41d4-a716-446655440005',
      dest_cohorte_id: '550e8400-e29b-41d4-a716-446655440006',
    };
    const result = cloneEquipoSchema.safeParse(data);
    expect(result.success).toBe(true);
  });

  it('rejects identical source and destination', () => {
    const data = {
      source_materia_id: '550e8400-e29b-41d4-a716-446655440001',
      source_carrera_id: '550e8400-e29b-41d4-a716-446655440002',
      source_cohorte_id: '550e8400-e29b-41d4-a716-446655440003',
      dest_materia_id: '550e8400-e29b-41d4-a716-446655440001',
      dest_carrera_id: '550e8400-e29b-41d4-a716-446655440002',
      dest_cohorte_id: '550e8400-e29b-41d4-a716-446655440003',
    };
    const result = cloneEquipoSchema.safeParse(data);
    expect(result.success).toBe(false);
  });
});

describe('vigenciaBulkSchema Validation', () => {
  it('accepts valid vigencia data', () => {
    const data = {
      materia_id: '550e8400-e29b-41d4-a716-446655440000',
      carrera_id: '550e8400-e29b-41d4-a716-446655440001',
      cohorte_id: '550e8400-e29b-41d4-a716-446655440002',
      vig_desde: '2026-03-01',
      vig_hasta: '2026-12-31',
    };
    const result = vigenciaBulkSchema.safeParse(data);
    expect(result.success).toBe(true);
  });
});

describe('exportEquipoSchema Validation', () => {
  it('accepts with at least one filter', () => {
    const data = { carrera_id: '550e8400-e29b-41d4-a716-446655440000' };
    const result = exportEquipoSchema.safeParse(data);
    expect(result.success).toBe(true);
  });

  it('rejects with no filters', () => {
    const data = {};
    const result = exportEquipoSchema.safeParse(data);
    expect(result.success).toBe(false);
  });
});
