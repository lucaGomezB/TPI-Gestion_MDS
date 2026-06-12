import { type ReactNode } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { createColoquioSchema, type CreateColoquioFormData } from '../types/schemas';

interface ConvocatoriaFormProps {
  onSubmit: (data: CreateColoquioFormData) => void;
  isSubmitting: boolean;
  materiasOptions: { value: string; label: string }[];
}

function ConvocatoriaForm({ onSubmit, isSubmitting, materiasOptions }: ConvocatoriaFormProps): ReactNode {
  const {
    register,
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<CreateColoquioFormData>({
    resolver: zodResolver(createColoquioSchema),
    defaultValues: {
      materia_id: '',
      titulo: '',
      dias: [{ fecha: '', cupos: 1 }],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'dias',
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 max-w-lg">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Materia</label>
        <select
          {...register('materia_id')}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">Seleccione una materia</option>
          {materiasOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        {errors.materia_id && <p className="text-sm text-red-600 mt-1">{errors.materia_id.message}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Título</label>
        <input
          {...register('titulo')}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          placeholder="Ej: Coloquio Julio 2026"
        />
        {errors.titulo && <p className="text-sm text-red-600 mt-1">{errors.titulo.message}</p>}
      </div>

      {/* Días dinámicos */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium text-gray-700">Días disponibles</label>
          <button
            type="button"
            onClick={() => append({ fecha: '', cupos: 1 })}
            className="text-sm font-medium text-blue-600 hover:text-blue-800"
          >
            + Agregar día
          </button>
        </div>
        {errors.dias && (
          <p className="text-sm text-red-600 mb-2">{errors.dias.message || errors.dias.root?.message}</p>
        )}
        <div className="space-y-3">
          {fields.map((field, index) => (
            <div key={field.id} className="flex items-center space-x-3">
              <div className="flex-1">
                <input
                  type="date"
                  {...register(`dias.${index}.fecha`)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
                {errors.dias?.[index]?.fecha && (
                  <p className="text-xs text-red-600 mt-1">{errors.dias[index]?.fecha?.message}</p>
                )}
              </div>
              <div className="w-24">
                <input
                  type="number"
                  min={1}
                  {...register(`dias.${index}.cupos`)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  placeholder="Cupos"
                />
                {errors.dias?.[index]?.cupos && (
                  <p className="text-xs text-red-600 mt-1">{errors.dias[index]?.cupos?.message}</p>
                )}
              </div>
              {fields.length > 1 && (
                <button
                  type="button"
                  onClick={() => remove(index)}
                  className="text-sm text-red-600 hover:text-red-800"
                >
                  Eliminar
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isSubmitting ? 'Guardando...' : 'Crear convocatoria'}
      </button>
    </form>
  );
}

export default ConvocatoriaForm;
