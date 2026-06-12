import type { ReactNode } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { Aviso, AvisoFormData } from '../types';

const avisoSchema = z.object({
  titulo: z.string().min(1, 'El título es obligatorio').max(200),
  contenido: z.string().min(1, 'El contenido es obligatorio'),
  alcance: z.enum(['Global', 'PorMateria', 'PorCohorte', 'PorRol']),
  contexto_id: z.string().optional(),
  roles_destino: z.array(z.string()).optional(),
  severidad: z.enum(['Info', 'Advertencia', 'Critico']),
  inicio_vigencia: z.string().min(1, 'La fecha de inicio es obligatoria'),
  fin_vigencia: z.string().min(1, 'La fecha de fin es obligatoria'),
  requiere_acuse: z.boolean(),
});

interface AvisoFormProps {
  onSubmit: (data: AvisoFormData) => void;
  isSubmitting?: boolean;
  initialData?: Aviso;
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
    defaultValues: initialData
      ? {
          titulo: initialData.titulo,
          contenido: initialData.contenido,
          alcance: initialData.alcance,
          contexto_id: initialData.contexto_id ?? '',
          roles_destino: initialData.roles_destino ?? [],
          severidad: initialData.severidad,
          inicio_vigencia: initialData.inicio_vigencia.slice(0, 16),
          fin_vigencia: initialData.fin_vigencia.slice(0, 16),
          requiere_acuse: initialData.requiere_acuse,
        }
      : {
          titulo: '',
          contenido: '',
          alcance: 'Global' as const,
          contexto_id: '',
          roles_destino: [],
          severidad: 'Info' as const,
          inicio_vigencia: '',
          fin_vigencia: '',
          requiere_acuse: false,
        },
  });

  const alcance = watch('alcance');
  const showContexto = alcance === 'PorMateria' || alcance === 'PorCohorte';
  const showRoles = alcance === 'PorRol';

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
        <label htmlFor="contenido" className="block text-sm font-medium text-gray-700 mb-1">
          Contenido
        </label>
        <textarea
          id="contenido"
          rows={6}
          {...register('contenido')}
          className={`w-full rounded-md border px-3 py-2 text-sm ${
            errors.contenido ? 'border-red-500' : 'border-gray-300'
          }`}
        />
        {errors.contenido && (
          <p className="mt-1 text-sm text-red-600">{errors.contenido.message}</p>
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
            <option value="Info">Información</option>
            <option value="Advertencia">Advertencia</option>
            <option value="Critico">Crítico</option>
          </select>
        </div>
      </div>

      {showContexto && (
        <div>
          <label htmlFor="contexto_id" className="block text-sm font-medium text-gray-700 mb-1">
            ID de contexto ({alcance === 'PorMateria' ? 'Materia' : 'Cohorte'})
          </label>
          <input
            id="contexto_id"
            type="text"
            {...register('contexto_id')}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            placeholder="UUID"
          />
        </div>
      )}

      {showRoles && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Roles destino
          </label>
          <div className="space-y-2">
            {['PROFESOR', 'TUTOR', 'COORDINADOR', 'ADMIN', 'NEXO', 'FINANZAS'].map((rol) => (
              <label key={rol} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  value={rol}
                  {...register('roles_destino')}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600"
                />
                <span className="text-sm text-gray-700">{rol}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="inicio_vigencia" className="block text-sm font-medium text-gray-700 mb-1">
            Inicio de vigencia
          </label>
          <input
            id="inicio_vigencia"
            type="datetime-local"
            {...register('inicio_vigencia')}
            className={`w-full rounded-md border px-3 py-2 text-sm ${
              errors.inicio_vigencia ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.inicio_vigencia && (
            <p className="mt-1 text-sm text-red-600">{errors.inicio_vigencia.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="fin_vigencia" className="block text-sm font-medium text-gray-700 mb-1">
            Fin de vigencia
          </label>
          <input
            id="fin_vigencia"
            type="datetime-local"
            {...register('fin_vigencia')}
            className={`w-full rounded-md border px-3 py-2 text-sm ${
              errors.fin_vigencia ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.fin_vigencia && (
            <p className="mt-1 text-sm text-red-600">{errors.fin_vigencia.message}</p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <input
          id="requiere_acuse"
          type="checkbox"
          {...register('requiere_acuse')}
          className="h-4 w-4 rounded border-gray-300 text-blue-600"
        />
        <label htmlFor="requiere_acuse" className="text-sm text-gray-700">
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
