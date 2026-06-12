import { describe, it, expect, vi, beforeEach } from 'vitest';
import api from '@/shared/services/api';
import {
  getConvocatorias,
  createConvocatoria,
  getAgenda,
  reservarTurno,
  registrarResultado,
  getMetricas,
} from '@/features/coloquios/services/coloquioService';

vi.mock('@/shared/services/api');
const mockedApi = vi.mocked(api);

beforeEach(() => {
  vi.clearAllMocks();
});

describe('coloquioService', () => {
  describe('getConvocatorias', () => {
    it('calls GET materias/{id}/coloquios with params', async () => {
      mockedApi.get.mockResolvedValue({ data: [] });
      const result = await getConvocatorias({ materia_id: 'm1' });
      expect(mockedApi.get).toHaveBeenCalledWith('/materias/m1/coloquios');
      expect(result).toEqual([]);
    });
  });

  describe('createConvocatoria', () => {
    it('calls POST materias/{id}/coloquios with payload', async () => {
      const payload = {
        materia_id: 'm1',
        titulo: 'Coloquio Julio',
        dias: [{ fecha: '2026-07-01', cupos: 10 }],
      };
      mockedApi.post.mockResolvedValue({ data: { id: 'col1' } });
      const result = await createConvocatoria(payload);
      const { materia_id: _m, ...expectedPayload } = payload;
      expect(mockedApi.post).toHaveBeenCalledWith('/materias/m1/coloquios', expectedPayload);
      expect(result).toEqual({ id: 'col1' });
    });
  });

  describe('getAgenda', () => {
    it('calls GET coloquios/{id}/agenda', async () => {
      mockedApi.get.mockResolvedValue({
        data: {
          convocatoria: { id: 'col1', materia_nombre: 'M1', titulo: 'C1', activa: true },
          dias: [],
        },
      });
      const result = await getAgenda('col1');
      expect(mockedApi.get).toHaveBeenCalledWith('/coloquios/col1/agenda');
      expect(result.convocatoria.id).toBe('col1');
    });
  });

  describe('reservarTurno', () => {
    it('calls POST coloquios/{id}/reservar', async () => {
      mockedApi.post.mockResolvedValue({ data: { id: 'r1' } });
      const result = await reservarTurno('col1', { dia_id: 'd1', alumno_id: 'a1' });
      expect(mockedApi.post).toHaveBeenCalledWith('/coloquios/col1/reservar', { dia_id: 'd1', alumno_id: 'a1' });
      expect(result).toEqual({ id: 'r1' });
    });
  });

  describe('registrarResultado', () => {
    it('calls POST coloquios/{id}/resultados', async () => {
      mockedApi.post.mockResolvedValue({ data: { id: 'res1' } });
      const result = await registrarResultado('col1', { alumno_id: 'a1', nota: 8, aprobado: true });
      expect(mockedApi.post).toHaveBeenCalledWith('/coloquios/col1/resultados', {
        alumno_id: 'a1',
        nota: 8,
        aprobado: true,
      });
      expect(result).toEqual({ id: 'res1' });
    });
  });

  describe('getMetricas', () => {
    it('calls GET admin/coloquios/metricas', async () => {
      const mockData = {
        total_convocatorias_activas: 5,
        total_alumnos_importados: 100,
        total_reservas_activas: 30,
        total_resultados_registrados: 20,
      };
      mockedApi.get.mockResolvedValue({ data: mockData });
      const result = await getMetricas();
      expect(mockedApi.get).toHaveBeenCalledWith('/admin/coloquios/metricas');
      expect(result).toEqual(mockData);
    });
  });
});
