import { describe, it, expect, vi, beforeEach } from 'vitest';
import api from '../../../src/shared/services/api';
import * as estructuraService from '../../../src/features/estructura-academica/services/estructuraService';

vi.mock('../../../src/shared/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

describe('estructuraService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getCarreras', () => {
    it('calls GET /admin/carreras', async () => {
      const mockData = [{ id: '1', codigo: 'LIC-INF', nombre: 'Lic. Informática', activo: true }];
      vi.mocked(api.get).mockResolvedValue({ data: mockData });

      const result = await estructuraService.getCarreras();
      expect(api.get).toHaveBeenCalledWith('/admin/carreras');
      expect(result).toEqual(mockData);
    });
  });

  describe('createCarrera', () => {
    it('calls POST /admin/carreras with payload', async () => {
      const payload = { codigo: 'LIC-INF', nombre: 'Lic. Informática' };
      vi.mocked(api.post).mockResolvedValue({ data: { id: '1', ...payload, activo: true } });

      const result = await estructuraService.createCarrera(payload);
      expect(api.post).toHaveBeenCalledWith('/admin/carreras', payload);
      expect(result.codigo).toBe('LIC-INF');
    });
  });

  describe('updateCarrera', () => {
    it('calls PUT /admin/carreras/{id} with payload', async () => {
      const payload = { nombre: 'Updated', activo: true };
      vi.mocked(api.put).mockResolvedValue({ data: { id: '1', codigo: 'LIC-INF', ...payload } });

      const result = await estructuraService.updateCarrera('1', payload);
      expect(api.put).toHaveBeenCalledWith('/admin/carreras/1', payload);
      expect(result.nombre).toBe('Updated');
    });
  });

  describe('getCohortes', () => {
    it('calls GET /admin/cohortes with optional params', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: [] });
      await estructuraService.getCohortes({ carrera_id: '1' });
      expect(api.get).toHaveBeenCalledWith('/admin/cohortes', { params: { carrera_id: '1' } });
    });

    it('calls GET without params when none provided', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: [] });
      await estructuraService.getCohortes();
      expect(api.get).toHaveBeenCalledWith('/admin/cohortes', { params: undefined });
    });
  });

  describe('createMateria', () => {
    it('calls POST /admin/materias with payload', async () => {
      const payload = { codigo: 'MAT-101', nombre: 'Matemática' };
      vi.mocked(api.post).mockResolvedValue({ data: { id: '1', ...payload, activo: true } });

      const result = await estructuraService.createMateria(payload);
      expect(api.post).toHaveBeenCalledWith('/admin/materias', payload);
      expect(result.codigo).toBe('MAT-101');
    });
  });

  describe('uploadPrograma', () => {
    it('calls POST /admin/programas-materia/upload with FormData', async () => {
      const file = new File(['pdf content'], 'programa.pdf', { type: 'application/pdf' });
      vi.mocked(api.post).mockResolvedValue({ data: { id: '1', filename: 'programa.pdf', titulo: 'Programa 2026' } });

      const result = await estructuraService.uploadPrograma('m1', 'c1', 'co1', 'Programa 2026', file);
      expect(api.post).toHaveBeenCalledWith(
        '/admin/programas-materia/upload',
        expect.any(FormData),
        { headers: { 'Content-Type': 'multipart/form-data' } },
      );
      expect(result.filename).toBe('programa.pdf');
    });
  });
});
