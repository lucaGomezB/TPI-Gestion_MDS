import { describe, it, expect, vi, beforeEach } from 'vitest';
import api from '@/shared/services/api';
import {
  getEncuentrosAdmin,
  createSlot,
  createUnico,
  updateEncuentro,
  generateEmbed,
} from '@/features/encuentros/services/encuentroService';

vi.mock('@/shared/services/api');
const mockedApi = vi.mocked(api);

beforeEach(() => {
  vi.clearAllMocks();
});

describe('encuentroService', () => {
  describe('getEncuentrosAdmin', () => {
    it('calls GET /api/admin/encuentros with query params', async () => {
      const mockData = { data: [], total: 0, page: 1, per_page: 10, total_pages: 0 };
      mockedApi.get.mockResolvedValue({ data: mockData });

      const result = await getEncuentrosAdmin({ materia_id: 'm1', estado: 'Programado', page: 1 });
      expect(mockedApi.get).toHaveBeenCalledWith('/admin/encuentros', {
        params: { materia_id: 'm1', estado: 'Programado', page: 1 },
      });
      expect(result).toEqual(mockData);
    });

    it('calls GET without optional params', async () => {
      mockedApi.get.mockResolvedValue({ data: { data: [], total: 0, page: 1, per_page: 10, total_pages: 0 } });
      await getEncuentrosAdmin({});
      expect(mockedApi.get).toHaveBeenCalledWith('/admin/encuentros', { params: {} });
    });
  });

  describe('createSlot', () => {
    it('calls POST slot endpoint with materia_id in path', async () => {
      const payload = {
        materia_id: 'm1',
        titulo: 'Slot Test',
        dia_semana: 'Lunes' as const,
        hora: '10:00',
        fecha_inicio: '2026-06-01',
        cant_semanas: 4,
      };
      mockedApi.post.mockResolvedValue({ data: { id: 's1' } });

      const result = await createSlot(payload);
      const { materia_id: _m, ...expectedPayload } = payload;
      expect(mockedApi.post).toHaveBeenCalledWith('/materias/m1/encuentros/slot', expectedPayload);
      expect(result).toEqual({ id: 's1' });
    });
  });

  describe('createUnico', () => {
    it('calls POST unico endpoint with materia_id in path', async () => {
      const payload = { materia_id: 'm1', titulo: 'Unico', fecha: '2026-06-01', hora: '10:00' };
      mockedApi.post.mockResolvedValue({ data: { id: 'u1' } });

      const result = await createUnico(payload);
      const { materia_id: _m, ...expectedPayload } = payload;
      expect(mockedApi.post).toHaveBeenCalledWith('/materias/m1/encuentros/unico', expectedPayload);
      expect(result).toEqual({ id: 'u1' });
    });
  });

  describe('updateEncuentro', () => {
    it('calls PUT encuentros/{id} with payload', async () => {
      mockedApi.put.mockResolvedValue({ data: { id: 'e1', estado: 'Realizado' } });
      const result = await updateEncuentro('e1', { estado: 'Realizado' });
      expect(mockedApi.put).toHaveBeenCalledWith('/encuentros/e1', { estado: 'Realizado' });
      expect(result).toEqual({ id: 'e1', estado: 'Realizado' });
    });
  });

  describe('generateEmbed', () => {
    it('calls POST embed endpoint with materia_id and formato', async () => {
      mockedApi.post.mockResolvedValue({ data: { snippet: '<p>Hola</p>', formato: 'html' } });
      const result = await generateEmbed('m1', 'html');
      expect(mockedApi.post).toHaveBeenCalledWith('/materias/m1/encuentros/embed', { formato: 'html' });
      expect(result).toEqual({ snippet: '<p>Hola</p>', formato: 'html' });
    });
  });
});
