import { describe, it, expect, vi, beforeEach } from 'vitest';
import api from '../../../src/shared/services/api';
import * as docentesService from '../../../src/features/equipos/services/docentesService';

vi.mock('../../../src/shared/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

describe('docentesService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getDocentes', () => {
    it('calls GET /admin/usuarios?rol=docente', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: [] });
      await docentesService.getDocentes();
      expect(api.get).toHaveBeenCalledWith('/admin/usuarios', { params: { rol: 'docente' } });
    });
  });

  describe('createDocente', () => {
    it('calls POST /admin/usuarios with payload', async () => {
      const payload = {
        nombre: 'Juan',
        apellidos: 'Pérez',
        email: 'juan@test.com',
        roles: ['PROFESOR'],
        regional: 'Córdoba',
      };
      vi.mocked(api.post).mockResolvedValue({ data: { id: '1', ...payload, activo: true } });

      const result = await docentesService.createDocente(payload);
      expect(api.post).toHaveBeenCalledWith('/admin/usuarios', payload);
      expect(result.email).toBe('juan@test.com');
    });
  });

  describe('updateDocente', () => {
    it('calls PUT /admin/usuarios/{id} with payload', async () => {
      const payload = {
        nombre: 'Juan',
        apellidos: 'Pérez',
        email: 'juan@test.com',
        roles: ['PROFESOR', 'TUTOR'],
        regional: 'Córdoba',
        activo: false,
      };
      vi.mocked(api.put).mockResolvedValue({ data: { id: '1', ...payload } });

      const result = await docentesService.updateDocente('1', payload);
      expect(api.put).toHaveBeenCalledWith('/admin/usuarios/1', payload);
      expect(result.activo).toBe(false);
    });
  });
});
