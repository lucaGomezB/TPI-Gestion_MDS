import { describe, it, expect } from 'vitest';

// Verify all page modules can be imported (lazy-loaded routes work)
describe('Equipos pages lazy loading', () => {
  it('imports MisEquiposPage without error', async () => {
    const mod = await import('../../../src/features/equipos/pages/MisEquiposPage');
    expect(mod.default).toBeDefined();
  });

  it('imports DocentesPage without error', async () => {
    const mod = await import('../../../src/features/equipos/pages/DocentesPage');
    expect(mod.default).toBeDefined();
  });

  it('imports AsignacionesPage without error', async () => {
    const mod = await import('../../../src/features/equipos/pages/AsignacionesPage');
    expect(mod.default).toBeDefined();
  });

  it('imports AsignacionMasivaPage without error', async () => {
    const mod = await import('../../../src/features/equipos/pages/AsignacionMasivaPage');
    expect(mod.default).toBeDefined();
  });

  it('imports CloneEquipoPage without error', async () => {
    const mod = await import('../../../src/features/equipos/pages/CloneEquipoPage');
    expect(mod.default).toBeDefined();
  });

  it('imports VigenciaPage without error', async () => {
    const mod = await import('../../../src/features/equipos/pages/VigenciaPage');
    expect(mod.default).toBeDefined();
  });

  it('imports ExportEquipoPage without error', async () => {
    const mod = await import('../../../src/features/equipos/pages/ExportEquipoPage');
    expect(mod.default).toBeDefined();
  });
});

describe('Estructura pages lazy loading', () => {
  it('imports CarrerasPage without error', async () => {
    const mod = await import('../../../src/features/estructura-academica/pages/CarrerasPage');
    expect(mod.default).toBeDefined();
  });

  it('imports CohortesPage without error', async () => {
    const mod = await import('../../../src/features/estructura-academica/pages/CohortesPage');
    expect(mod.default).toBeDefined();
  });

  it('imports MateriasPage without error', async () => {
    const mod = await import('../../../src/features/estructura-academica/pages/MateriasPage');
    expect(mod.default).toBeDefined();
  });
});
