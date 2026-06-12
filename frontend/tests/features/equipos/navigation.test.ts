import { describe, it, expect } from 'vitest';
import { navigationConfig } from '../../../src/shared/config/navigation';

describe('Navigation Config - Equipos Routes', () => {
  it('includes Mis Equipos under Académico for docente roles', () => {
    const academico = navigationConfig.find((s) => s.title === 'Académico');
    expect(academico).toBeDefined();

    const misEquipos = academico!.items.find((i) => i.label === 'Mis Equipos');
    expect(misEquipos).toBeDefined();
    expect(misEquipos!.path).toBe('/mis-equipos');
    expect(misEquipos!.permissions).toContain('PROFESOR');
    expect(misEquipos!.permissions).toContain('TUTOR');
    expect(misEquipos!.permissions).toContain('NEXO');
    expect(misEquipos!.permissions).toContain('COORDINADOR');
  });

  it('includes Equipos section with Asignaciones and Docentes', () => {
    const equipos = navigationConfig.find((s) => s.title === 'Equipos');
    expect(equipos).toBeDefined();

    const asignaciones = equipos!.items.find((i) => i.label === 'Asignaciones');
    expect(asignaciones).toBeDefined();
    expect(asignaciones!.path).toBe('/admin/equipos/asignaciones');
    expect(asignaciones!.permissions).toEqual(['ADMIN', 'COORDINADOR']);

    const docentes = equipos!.items.find((i) => i.label === 'Docentes');
    expect(docentes).toBeDefined();
    expect(docentes!.path).toBe('/admin/equipos/docentes');
    expect(docentes!.permissions).toEqual(['ADMIN']);
  });

  it('includes Carreras, Cohortes, Materias under Administración', () => {
    const admin = navigationConfig.find((s) => s.title === 'Administración');
    expect(admin).toBeDefined();

    const carreras = admin!.items.find((i) => i.label === 'Carreras');
    expect(carreras).toBeDefined();
    expect(carreras!.path).toBe('/admin/estructura/carreras');
    expect(carreras!.permissions).toEqual(['ADMIN']);

    const cohortes = admin!.items.find((i) => i.label === 'Cohortes');
    expect(cohortes).toBeDefined();
    expect(cohortes!.path).toBe('/admin/estructura/cohortes');

    const materias = admin!.items.find((i) => i.label === 'Materias (Admin)');
    expect(materias).toBeDefined();
    expect(materias!.path).toBe('/admin/estructura/materias');
    expect(materias!.permissions).toEqual(['ADMIN', 'COORDINADOR']);
  });
});
