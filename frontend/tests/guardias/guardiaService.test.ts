import { describe, it, expect, vi, beforeEach } from 'vitest';
import api from '@/shared/services/api';
import { getGuardias, createGuardia } from '@/features/guardias/services/guardiaService';

vi.mock('@/shared/services/api');
const mockedApi = vi.mocked(api);

beforeEach(() => {
  vi.clearAllMocks();
});

describe('guardiaService', () => {
  describe('getGuardias', () => {
    it('calls GET materias/{id}/guardias with filters', async () => {
      mockedApi.get.mockResolvedValue({
        data: { data: [], total: 0, page: 1, per_page: 10, total_pages: 0 },
      });
      const result = await getGuardias('m1', { estado: 'Pendiente', page: 1 });
      expect(mockedApi.get).toHaveBeenCalledWith('/materias/m1/guardias', {
        params: { estado: 'Pendiente', page: 1 },
      });
      expect(result).toEqual({ data: [], total: 0, page: 1, per_page: 10, total_pages: 0 });
    });

    it('calls GET without filters', async () => {
      mockedApi.get.mockResolvedValue({
        data: { data: [], total: 0, page: 1, per_page: 10, total_pages: 0 },
      });
      await getGuardias('m1', {});
      expect(mockedApi.get).toHaveBeenCalledWith('/materias/m1/guardias', { params: {} });
    });
  });

  describe('createGuardia', () => {
    it('calls POST materias/{id}/guardias with payload', async () => {
      const payload = {
        asignacion_id: 'a1',
        carrera_id: 'c1',
        cohorte_id: 'ch1',
        dia: 'Lunes' as const,
        horario: '14:00-14:45',
      };
      mockedApi.post.mockResolvedValue({ data: { id: 'g1' } });
      const result = await createGuardia('m1', payload);
      expect(mockedApi.post).toHaveBeenCalledWith('/materias/m1/guardias', payload);
      expect(result).toEqual({ id: 'g1' });
    });
  });
});
