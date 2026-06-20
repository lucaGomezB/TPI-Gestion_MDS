import type { ReactNode } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { Aviso, AvisoFormData, SeveridadAviso, AlcanceAviso } from '../types';

const avisoSchema = z.object({
  titulo: z.string().min(1, 'El título es obligatorio').max(200),
  cuerpo: z.string().min(1, 'El contenido es obligatorio'),
  alcance: z.enum(['Global', 'PorMateria', 'PorCohorte', 'PorRol']),
  materia_id: z.string().optional(),
  cohorte_id: z.string().optional(),
  rol_destino: z.string().optional(),
  severidad: z.enum(['Baja', 'Media', 'Alta', 'Critico']),
  inicio_en: z.string().min(1, 'La fecha de inicio es obligatoria'),
  fin_en: z.string().min(1, 'La fecha de fin es obligatoria'),
  orden: z.number().int().min(0).optional(),
  activo: z.boolean().optional(),
  requiere_ack: z.boolean().optional(),
});

interface AvisoFormProps {
  onSubmit: (data: AvisoFormData) => void;
  isSubmitting?: boolean;
  initialData?: Aviso;
}

function buildDefaultValues(initialData?: Aviso): AvisoFormData {
  if (initialData) {
    return {
      titulo: initialData.titulo,
      cuerpo: initialData.cuerpo,
      alcance: initialData.alcance as AlcanceAviso,
      materia_id: initialData.materia_id ?? undefined,
      cohorte_id: initialData.cohorte_id ?? undefined,
      rol_destino: initialData.rol_destino ?? undefined,
      severidad: initialData.severidad as SeveridadAviso,
      inicio_en: initialData.inicio_en.slice(0, 16),
      fin_en: initialData.fin_en.slice(0, 16),
      orden: initialData.orden,
      activo: initialData.activo,
      requiere_ack: initialData.requiere_ack,
    };
  }
  return {
    titulo: '',
    cuerpo: '',
    alcance: 'Global',
    materia_id: undefined,
    cohorte_id: undefined,
    rol_destino: undefined,
    severidad: 'Baja',
    inicio_en: '',
    fin_en: '',
    orden: 0,
    activo: true,
    requiere_ack: false,
  };
}

function AvisoForm({
  onSubmit,
  isSubmitting = false,
  initialData,
}: AvisoFormProps): ReactNode {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<AvisoFormData>({
    resolver: zodResolver(avisoSchema),
    defaultValues: buildDefaultValues(initialData),
  });

  const alcance = watch('alcance');
  const showMateria = alcance === 'PorMateria';
  const showCohorte = alcance === 'PorCohorte';
  const showRol = alcance === 'PorRol';

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 max-w-2xl">
      <div>
        <label htmlFor="titulo" className="block text-sm font-medium text-gray-700 mb-1">
          Título
        </label>
        <input
          id="titulo"
          type="text"
          {...register('titulo')}
          className={`w-full rounded-md border px-3 py-2 text-sm ${
            errors.titulo ? 'border-red-500' : 'border-gray-300'
          }`}
        />
        {errors.titulo && <p className="mt-1 text-sm text-red-600">{errors.titulo.message}</p>}
      </div>

      <div>
        <label htmlFor="cuerpo" className="block text-sm font-medium text-gray-700 mb-1">
          Contenido
        </label>
        <textarea
          id="cuerpo"
          rows={6}
          {...register('cuerpo')}
          className={`w-full rounded-md border px-3 py-2 text-sm ${
            errors.cuerpo ? 'border-red-500' : 'border-gray-300'
          }`}
        />
        {errors.cuerpo && (
          <p className="mt-1 text-sm text-red-600">{errors.cuerpo.message}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="alcance" className="block text-sm font-medium text-gray-700 mb-1">
            Alcance
          </label>
          <select
            id="alcance"
            {...register('alcance')}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="Global">Global</option>
            <option value="PorMateria">Por Materia</option>
            <option value="PorCohorte">Por Cohorte</option>
            <option value="PorRol">Por Rol</option>
          </select>
        </div>

        <div>
          <label htmlFor="severidad" className="block text-sm font-medium text-gray-700 mb-1">
            Severidad
          </label>
          <select
            id="severidad"
            {...register('severidad')}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="Baja">Baja</option>
            <option value="Media">Media</option>
            <option value="Alta">Alta</option>
            <option value="Critico">Crítico</option>
          </select>
        </div>
      </div>

      {showMateria && (
        <div>
          <label htmlFor="materia_id" className="block text-sm font-medium text-gray-700 mb-1">
            ID de Materia
          </label>
          <input
            id="materia_id"
            type="text"
            {...register('materia_id')}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            placeholder="UUID"
          />
        </div>
      )}

      {showCohorte && (
        <div>
          <label htmlFor="cohorte_id" className="block text-sm font-medium text-gray-700 mb-1">
            ID de Cohorte
          </label>
          <input
            id="cohorte_id"
            type="text"
            {...register('cohorte_id')}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            placeholder="UUID"
          />
        </div>
      )}

      {showRol && (
        <div>
          <label htmlFor="rol_destino" className="block text-sm font-medium text-gray-700 mb-1">
            Rol destino
          </label>
          <select
            id="rol_destino"
            {...register('rol_destino')}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">Seleccione un rol</option>
            {['PROFESOR', 'TUTOR', 'COORDINADOR', 'ADMIN', 'NEXO', 'FINANZAS'].map((rol) => (
              <option key={rol} value={rol}>{rol}</option>
            ))}
          </select>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="inicio_en" className="block text-sm font-medium text-gray-700 mb-1">
            Inicio de vigencia
          </label>
          <input
            id="inicio_en"
            type="datetime-local"
            {...register('inicio_en')}
            className={`w-full rounded-md border px-3 py-2 text-sm ${
              errors.inicio_en ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.inicio_en && (
            <p className="mt-1 text-sm text-red-600">{errors.inicio_en.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="fin_en" className="block text-sm font-medium text-gray-700 mb-1">
            Fin de vigencia
          </label>
          <input
            id="fin_en"
            type="datetime-local"
            {...register('fin_en')}
            className={`w-full rounded-md border px-3 py-2 text-sm ${
              errors.fin_en ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.fin_en && (
            <p className="mt-1 text-sm text-red-600">{errors.fin_en.message}</p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <input
          id="requiere_ack"
          type="checkbox"
          {...register('requiere_ack')}
          className="h-4 w-4 rounded border-gray-300 text-blue-600"
        />
        <label htmlFor="requiere_ack" className="text-sm text-gray-700">
          Requiere confirmación de lectura
        </label>
      </div>

      <div className="flex justify-end gap-3">
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {isSubmitting ? 'Guardando...' : initialData ? 'Actualizar aviso' : 'Crear aviso'}
        </button>
      </div>
    </form>
  );
}

export default AvisoForm;
