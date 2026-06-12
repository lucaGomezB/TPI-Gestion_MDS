import { type ReactNode } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { createGuardiaSchema, type CreateGuardiaFormData } from '../types/schemas';

interface GuardiaFormProps {
  onSubmit: (data: CreateGuardiaFormData) => void;
  isSubmitting: boolean;
  carreraOptions: { value: string; label: string }[];
  cohorteOptions: { value: string; label: string }[];
  asignacionOptions: { value: string; label: string }[];
}

function GuardiaForm({ onSubmit, isSubmitting, carreraOptions, cohorteOptions, asignacionOptions }: GuardiaFormProps): ReactNode {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CreateGuardiaFormData>({
    resolver: zodResolver(createGuardiaSchema),
  });

  const diaSemanaOptions = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 max-w-lg">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Asignación / Docente</label>
        <select
          {...register('asignacion_id')}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">Seleccione una asignación</option>
          {asignacionOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        {errors.asignacion_id && <p className="text-sm text-red-600 mt-1">{errors.asignacion_id.message}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Carrera</label>
        <select
          {...register('carrera_id')}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">Seleccione una carrera</option>
          {carreraOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        {errors.carrera_id && <p className="text-sm text-red-600 mt-1">{errors.carrera_id.message}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Cohorte</label>
        <select
          {...register('cohorte_id')}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">Seleccione un cohorte</option>
          {cohorteOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        {errors.cohorte_id && <p className="text-sm text-red-600 mt-1">{errors.cohorte_id.message}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Día</label>
        <select
          {...register('dia')}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">Seleccione un día</option>
          {diaSemanaOptions.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
        {errors.dia && <p className="text-sm text-red-600 mt-1">{errors.dia.message}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Horario</label>
        <input
          {...register('horario')}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          placeholder="Ej: 14:00-14:45"
        />
        {errors.horario && <p className="text-sm text-red-600 mt-1">{errors.horario.message}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Comentarios <span className="text-gray-400">(opcional)</span>
        </label>
        <textarea
          {...register('comentarios')}
          rows={3}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          placeholder="Comentarios adicionales..."
        />
        {errors.comentarios && <p className="text-sm text-red-600 mt-1">{errors.comentarios.message}</p>}
      </div>

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

export default GuardiaForm;
