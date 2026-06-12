import type { ReactNode } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const comunicacionSchema = z.object({
  asunto: z.string().min(1, 'El asunto es obligatorio').max(200, 'El asunto no puede exceder 200 caracteres'),
  cuerpo: z.string().min(1, 'El cuerpo del mensaje es obligatorio'),
  requiere_aprobacion: z.boolean().optional(),
  materia_id: z.string().min(1, 'La materia es obligatoria'),
});

export type ComunicacionFormValues = z.infer<typeof comunicacionSchema>;

interface ComunicacionFormProps {
  materias: Array<{ id: string; nombre: string }>;
  onSubmit: (data: ComunicacionFormValues) => void;
  isSubmitting?: boolean;
  defaultValues?: Partial<ComunicacionFormValues>;
}

function ComunicacionForm({
  materias,
  onSubmit,
  isSubmitting = false,
  defaultValues,
}: ComunicacionFormProps): ReactNode {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ComunicacionFormValues>({
    resolver: zodResolver(comunicacionSchema),
    defaultValues: {
      asunto: '',
      cuerpo: '',
      requiere_aprobacion: false,
      materia_id: '',
      ...defaultValues,
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <label htmlFor="materia_id" className="block text-sm font-medium text-gray-700 mb-1">
          Materia
        </label>
        <select
          id="materia_id"
          {...register('materia_id')}
          className={`w-full rounded-md border px-3 py-2 text-sm ${
            errors.materia_id ? 'border-red-500' : 'border-gray-300'
          }`}
        >
          <option value="">Seleccione una materia</option>
          {materias.map((m) => (
            <option key={m.id} value={m.id}>
              {m.nombre}
            </option>
          ))}
        </select>
        {errors.materia_id && (
          <p className="mt-1 text-sm text-red-600">{errors.materia_id.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="asunto" className="block text-sm font-medium text-gray-700 mb-1">
          Asunto
        </label>
        <input
          id="asunto"
          type="text"
          {...register('asunto')}
          className={`w-full rounded-md border px-3 py-2 text-sm ${
            errors.asunto ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="Ej: Recordatorio de entrega TP"
        />
        {errors.asunto && (
          <p className="mt-1 text-sm text-red-600">{errors.asunto.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="cuerpo" className="block text-sm font-medium text-gray-700 mb-1">
          Cuerpo del mensaje
        </label>
        <p className="text-xs text-gray-500 mb-2">
          Use {'{{alumno.nombre}}'} para el nombre del alumno y {'{{materia.nombre}}'} para el nombre de la materia.
        </p>
        <textarea
          id="cuerpo"
          rows={8}
          {...register('cuerpo')}
          className={`w-full rounded-md border px-3 py-2 text-sm ${
            errors.cuerpo ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="Estimado/a {{alumno.nombre}}, le recordamos que la materia {{materia.nombre}} tiene..."
        />
        {errors.cuerpo && (
          <p className="mt-1 text-sm text-red-600">{errors.cuerpo.message}</p>
        )}
      </div>

      <div className="flex items-center gap-2">
        <input
          id="requiere_aprobacion"
          type="checkbox"
          {...register('requiere_aprobacion')}
          className="h-4 w-4 rounded border-gray-300 text-blue-600"
        />
        <label htmlFor="requiere_aprobacion" className="text-sm text-gray-700">
          Requiere aprobación antes del envío
        </label>
      </div>

      <div className="flex justify-end gap-3">
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {isSubmitting ? 'Procesando...' : 'Vista previa'}
        </button>
      </div>
    </form>
  );
}

export default ComunicacionForm;
