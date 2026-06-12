import { type ReactNode } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { createSlotSchema, createUnicoSchema, type CreateSlotFormData, type CreateUnicoFormData } from '../types/schemas';

type Modo = 'recurrente' | 'unico';

interface EncuentroFormProps {
  modo: Modo;
  onModoChange: (modo: Modo) => void;
  onSubmit: (data: CreateSlotFormData | CreateUnicoFormData) => void;
  isSubmitting: boolean;
  materiasOptions: { value: string; label: string }[];
}

function EncuentroForm({ modo, onModoChange, onSubmit, isSubmitting, materiasOptions }: EncuentroFormProps): ReactNode {
  const schema = modo === 'recurrente' ? createSlotSchema : createUnicoSchema;

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CreateSlotFormData | CreateUnicoFormData>({
    resolver: zodResolver(schema),
  });

  const diaSemanaOptions = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 max-w-lg">
      {/* Toggle modo */}
      <div className="flex space-x-2">
        <button
          type="button"
          onClick={() => onModoChange('recurrente')}
          className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
            modo === 'recurrente'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Slot recurrente
        </button>
        <button
          type="button"
          onClick={() => onModoChange('unico')}
          className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
            modo === 'unico'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Encuentro único
        </button>
      </div>

      {/* Materia */}
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

      {/* Título */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Título</label>
        <input
          {...register('titulo')}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          placeholder="Ej: Clase 1 - Introducción"
        />
        {errors.titulo && <p className="text-sm text-red-600 mt-1">{errors.titulo.message}</p>}
      </div>

      {/* Hora */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Hora</label>
        <input
          type="time"
          {...register('hora')}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        />
        {errors.hora && <p className="text-sm text-red-600 mt-1">{errors.hora.message}</p>}
      </div>

      {/* Campos específicos según modo */}
      {modo === 'recurrente' && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Día de la semana</label>
            <select
              {...register('dia_semana')}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="">Seleccione un día</option>
              {diaSemanaOptions.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
            {errors.dia_semana && <p className="text-sm text-red-600 mt-1">{errors.dia_semana.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Fecha de inicio</label>
            <input
              type="date"
              {...register('fecha_inicio')}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
            {errors.fecha_inicio && <p className="text-sm text-red-600 mt-1">{errors.fecha_inicio.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cantidad de semanas</label>
            <input
              type="number"
              min={0}
              {...register('cant_semanas')}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              placeholder="0 = ilimitado"
            />
            {errors.cant_semanas && <p className="text-sm text-red-600 mt-1">{errors.cant_semanas.message}</p>}
          </div>
        </>
      )}

      {modo === 'unico' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Fecha</label>
          <input
            type="date"
            {...register('fecha')}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          />
          {errors.fecha && <p className="text-sm text-red-600 mt-1">{errors.fecha.message}</p>}
        </div>
      )}

      {/* Meet URL */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Meet URL <span className="text-gray-400">(opcional)</span>
        </label>
        <input
          {...register('meet_url')}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          placeholder="https://meet.google.com/..."
        />
        {errors.meet_url && <p className="text-sm text-red-600 mt-1">{errors.meet_url.message}</p>}
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isSubmitting ? 'Guardando...' : 'Guardar'}
      </button>
    </form>
  );
}

export default EncuentroForm;
