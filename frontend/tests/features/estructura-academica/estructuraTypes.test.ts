import { describe, it, expect } from 'vitest';
import {
  createCarreraSchema,
  createCohorteSchema,
  createMateriaSchema,
  uploadProgramaSchema,
} from '../../../src/features/estructura-academica/types/estructura';

describe('Carrera Schema Validation', () => {
  it('accepts valid carrera data', () => {
    const data = { codigo: 'LIC-INF', nombre: 'Licenciatura en Informática' };
    const result = createCarreraSchema.safeParse(data);
    expect(result.success).toBe(true);
  });

  it('rejects empty codigo', () => {
    const data = { codigo: '', nombre: 'Test' };
    const result = createCarreraSchema.safeParse(data);
    expect(result.success).toBe(false);
  });

  it('rejects empty nombre', () => {
    const data = { codigo: 'TEST', nombre: '' };
    const result = createCarreraSchema.safeParse(data);
    expect(result.success).toBe(false);
  });
});

describe('Cohorte Schema Validation', () => {
  const validCohorte = {
    carrera_id: '550e8400-e29b-41d4-a716-446655440000',
    nombre: 'MAR-2026',
    anio_inicio: 2026,
    vig_desde: '2026-03-01',
    vig_hasta: '2026-12-31',
  };

  it('accepts valid cohorte data', () => {
    const result = createCohorteSchema.safeParse(validCohorte);
    expect(result.success).toBe(true);
  });

  it('rejects invalid date format', () => {
    const data = { ...validCohorte, vig_desde: '01-03-2026' };
    const result = createCohorteSchema.safeParse(data);
    expect(result.success).toBe(false);
  });

  it('rejects anio_inicio out of range', () => {
    const data = { ...validCohorte, anio_inicio: 1999 };
    const result = createCohorteSchema.safeParse(data);
    expect(result.success).toBe(false);
  });
});

describe('Materia Schema Validation', () => {
  it('accepts valid materia data', () => {
    const data = { codigo: 'MAT-101', nombre: 'Matemática I' };
    const result = createMateriaSchema.safeParse(data);
    expect(result.success).toBe(true);
  });
});

describe('uploadProgramaSchema Validation', () => {
  it('rejects non-PDF file', () => {
    const file = new File(['content'], 'test.txt', { type: 'text/plain' });
    const data = {
      materia_id: '550e8400-e29b-41d4-a716-446655440000',
      carrera_id: '550e8400-e29b-41d4-a716-446655440001',
      cohorte_id: '550e8400-e29b-41d4-a716-446655440002',
      titulo: 'Programa 2026',
      file,
    };
    const result = uploadProgramaSchema.safeParse(data);
    expect(result.success).toBe(false);
  });

  it('rejects oversized file', () => {
    const oversizedBuffer = new ArrayBuffer(11 * 1024 * 1024);
    const file = new File([oversizedBuffer], 'large.pdf', { type: 'application/pdf' });
    const data = {
      materia_id: '550e8400-e29b-41d4-a716-446655440000',
      carrera_id: '550e8400-e29b-41d4-a716-446655440001',
      cohorte_id: '550e8400-e29b-41d4-a716-446655440002',
      titulo: 'Programa 2026',
      file,
    };
    const result = uploadProgramaSchema.safeParse(data);
    expect(result.success).toBe(false);
  });
});
