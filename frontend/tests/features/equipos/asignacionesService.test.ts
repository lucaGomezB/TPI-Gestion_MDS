import { describe, it, expect, vi, beforeEach } from 'vitest';
import api from '../../../src/shared/services/api';
import * as asignacionesService from '../../../src/features/equipos/services/asignacionesService';

vi.mock('../../../src/shared/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

describe('asignacionesService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getAsignaciones', () => {
    it('calls GET /admin/asignaciones with filter params', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: [] });
      await asignacionesService.getAsignaciones({ rol: 'PROFESOR', search: 'Juan' });
      expect(api.get).toHaveBeenCalledWith('/admin/asignaciones', {
        params: { rol: 'PROFESOR', search: 'Juan' },
      });
    });
  });

  describe('createAsignacion', () => {
    it('calls POST /admin/asignaciones with payload', async () => {
      const payload = {
        docente_id: 'd1',
        materia_id: 'm1',
        carrera_id: 'c1',
        cohorte_id: 'co1',
        rol: 'PROFESOR',
        comisiones: ['A', 'B'],
        responsable_id: null,
        vig_desde: '2026-01-01',
        vig_hasta: '2026-12-31',
      };
      vi.mocked(api.post).mockResolvedValue({ data: { id: '1', ...payload, activo: true } });

      const result = await asignacionesService.createAsignacion(payload);
      expect(api.post).toHaveBeenCalledWith('/admin/asignaciones', payload);
      expect(result.rol).toBe('PROFESOR');
    });
  });

  describe('createAsignacionMasiva', () => {
    it('calls POST /admin/asignaciones/masiva', async () => {
      const payload = {
        docente_ids: ['d1', 'd2'],
        materia_id: 'm1',
        carrera_id: 'c1',
        cohorte_id: 'co1',
        rol: 'TUTOR',
        comisiones: [],
        responsable_id: null,
        vig_desde: '2026-01-01',
        vig_hasta: '2026-12-31',
      };
      vi.mocked(api.post).mockResolvedValue({ data: { count: 2 } });

      const result = await asignacionesService.createAsignacionMasiva(payload);
      expect(api.post).toHaveBeenCalledWith('/admin/asignaciones/masiva', payload);
      expect(result.count).toBe(2);
    });
  });

  describe('cloneEquipo', () => {
    it('calls POST /admin/asignaciones/clonar', async () => {
      const payload = {
        source_materia_id: 'm1',
        source_carrera_id: 'c1',
        source_cohorte_id: 'co1',
        dest_materia_id: 'm2',
        dest_carrera_id: 'c2',
        dest_cohorte_id: 'co2',
      };
      vi.mocked(api.post).mockResolvedValue({ data: { count: 5 } });

      const result = await asignacionesService.cloneEquipo(payload);
      expect(api.post).toHaveBeenCalledWith('/admin/asignaciones/clonar', payload);
      expect(result.count).toBe(5);
    });
  });

  describe('updateVigenciaBulk', () => {
    it('calls PUT /admin/asignaciones/vigencia', async () => {
      const payload = {
        materia_id: 'm1',
        carrera_id: 'c1',
        cohorte_id: 'co1',
        vig_desde: '2026-06-01',
        vig_hasta: '2026-12-31',
      };
      vi.mocked(api.put).mockResolvedValue({ data: { count: 3 } });

      const result = await asignacionesService.updateVigenciaBulk(payload);
      expect(api.put).toHaveBeenCalledWith('/admin/asignaciones/vigencia', payload);
      expect(result.count).toBe(3);
    });
  });

  describe('exportEquipo', () => {
    it('calls GET /admin/equipos/export with params and returns blob', async () => {
      const blob = new Blob(['csv content'], { type: 'text/csv' });
      vi.mocked(api.get).mockResolvedValue({ data: blob });
      const params = { carrera_id: 'c1' };

      const result = await asignacionesService.exportEquipo(params);
      expect(api.get).toHaveBeenCalledWith('/admin/equipos/export', {
        params,
        responseType: 'blob',
      });
      expect(result).toBeInstanceOf(Blob);
    });
  });

  describe('getMisEquipos', () => {
    it('calls GET /mis-equipos', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: [] });
      await asignacionesService.getMisEquipos();
      expect(api.get).toHaveBeenCalledWith('/mis-equipos');
    });
  });
});
