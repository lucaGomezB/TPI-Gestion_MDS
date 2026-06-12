import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { createCohorteSchema, type CreateCohorteData, type Cohorte } from '../types/estructura';
import type { Carrera } from '../types/estructura';

interface CohorteFormProps {
  onSubmit: (data: CreateCohorteData) => void;
  onCancel: () => void;
  initialData?: Cohorte;
  isSubmitting?: boolean;
  carreras: Carrera[];
}

function CohorteForm({ onSubmit, onCancel, initialData, isSubmitting, carreras }: CohorteFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CreateCohorteData>({
    resolver: zodResolver(createCohorteSchema),
    defaultValues: initialData
      ? {
          carrera_id: initialData.carrera_id,
          nombre: initialData.nombre,
          anio_inicio: initialData.anio_inicio,
          vig_desde: initialData.vig_desde,
          vig_hasta: initialData.vig_hasta,
        }
      : {
          carrera_id: '',
          nombre: '',
          anio_inicio: new Date().getFullYear(),
          vig_desde: '',
          vig_hasta: '',
        },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="carrera_id" className="block text-sm font-medium text-gray-700 mb-1">
          Carrera
        </label>
        <select
          id="carrera_id"
          {...register('carrera_id')}
          className={`w-full px-3 py-2 border rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
            errors.carrera_id ? 'border-red-500' : 'border-gray-300'
          }`}
        >
          <option value="">Seleccione una carrera</option>
          {carreras.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre} ({c.codigo})
            </option>
          ))}
        </select>
        {errors.carrera_id && (
          <p className="mt-1 text-xs text-red-600">{errors.carrera_id.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="nombre" className="block text-sm font-medium text-gray-700 mb-1">
          Nombre
        </label>
        <input
          id="nombre"
          type="text"
          {...register('nombre')}
          className={`w-full px-3 py-2 border rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
            errors.nombre ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="Ej: MAR-2026"
        />
        {errors.nombre && (
          <p className="mt-1 text-xs text-red-600">{errors.nombre.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="anio_inicio" className="block text-sm font-medium text-gray-700 mb-1">
          Año de Inicio
        </label>
        <input
          id="anio_inicio"
          type="number"
          {...register('anio_inicio', { valueAsNumber: true })}
          className={`w-full px-3 py-2 border rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
            errors.anio_inicio ? 'border-red-500' : 'border-gray-300'
          }`}
          min={2000}
          max={2100}
        />
        {errors.anio_inicio && (
          <p className="mt-1 text-xs text-red-600">{errors.anio_inicio.message}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="vig_desde" className="block text-sm font-medium text-gray-700 mb-1">
            Vigencia Desde
          </label>
          <input
            id="vig_desde"
            type="date"
            {...register('vig_desde')}
            className={`w-full px-3 py-2 border rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.vig_desde ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.vig_desde && (
            <p className="mt-1 text-xs text-red-600">{errors.vig_desde.message}</p>
          )}
        </div>
        <div>
          <label htmlFor="vig_hasta" className="block text-sm font-medium text-gray-700 mb-1">
            Vigencia Hasta
          </label>
          <input
            id="vig_hasta"
            type="date"
            {...register('vig_hasta')}
            className={`w-full px-3 py-2 border rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.vig_hasta ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.vig_hasta && (
            <p className="mt-1 text-xs text-red-600">{errors.vig_hasta.message}</p>
          )}
        </div>
      </div>

      <div className="flex items-center justify-end space-x-3 pt-2">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting ? 'Guardando...' : initialData ? 'Actualizar' : 'Crear'}
        </button>
      </div>
    </form>
  );
}

export default CohorteForm;
