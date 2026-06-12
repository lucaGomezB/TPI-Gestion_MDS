import { describe, it, expect } from 'vitest';
import { createDocenteSchema, DOCENTE_ROLES, REGIONALES } from '../../../src/features/equipos/types/docentes';

describe('Docente Schema Validation', () => {
  const validDocente = {
    nombre: 'Juan',
    apellidos: 'Pérez',
    email: 'juan@test.com',
    roles: ['PROFESOR'],
    regional: 'Córdoba',
  };

  it('accepts valid docente data', () => {
    const result = createDocenteSchema.safeParse(validDocente);
    expect(result.success).toBe(true);
  });

  it('rejects missing nombre', () => {
    const data = { ...validDocente, nombre: '' };
    const result = createDocenteSchema.safeParse(data);
    expect(result.success).toBe(false);
  });

  it('rejects invalid email', () => {
    const data = { ...validDocente, email: 'not-an-email' };
    const result = createDocenteSchema.safeParse(data);
    expect(result.success).toBe(false);
  });

  it('rejects empty roles array', () => {
    const data = { ...validDocente, roles: [] };
    const result = createDocenteSchema.safeParse(data);
    expect(result.success).toBe(false);
  });

  it('accepts without regional (defaults to empty string)', () => {
    const data = { ...validDocente };
    delete data.regional;
    const result = createDocenteSchema.safeParse(data);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.regional).toBe('');
    }
  });
});

describe('DOCENTE_ROLES', () => {
  it('contains all expected roles', () => {
    const roles = DOCENTE_ROLES.map((r) => r.value);
    expect(roles).toContain('PROFESOR');
    expect(roles).toContain('TUTOR');
    expect(roles).toContain('NEXO');
    expect(roles).toContain('COORDINADOR');
  });
});

describe('REGIONALES', () => {
  it('contains common regional values', () => {
    expect(REGIONALES).toContain('Capital Federal');
    expect(REGIONALES).toContain('Córdoba');
    expect(REGIONALES).toContain('Mendoza');
  });
});
