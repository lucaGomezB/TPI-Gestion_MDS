import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Button from '../../../shared/components/Button';
import type { TareaResponse } from '../types';

const tareaFormSchema = z.object({
  asignado_a: z
    .string()
    .min(1, 'El usuario asignado es requerido')
    .uuid('Debe ser un UUID valido'),
  descripcion: z
    .string()
    .min(1, 'La descripcion es requerida')
    .max(2000, 'Maximo 2000 caracteres'),
  materia_id: z
    .union([
      z.string().uuid('Debe ser un UUID valido'),
      z.literal(''),
    ])
    .optional(),
  contexto_id: z
    .union([
      z.string().uuid('Debe ser un UUID valido'),
      z.literal(''),
    ])
    .optional(),
});

export type TareaFormValues = z.infer<typeof tareaFormSchema>;

interface TareaFormProps {
  onSubmit: (data: TareaFormValues) => void;
  onCancel: () => void;
  initialData?: TareaResponse;
  isSubmitting?: boolean;
}

function TareaForm({
  onSubmit,
  onCancel,
  initialData,
  isSubmitting,
}: TareaFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<TareaFormValues>({
    resolver: zodResolver(tareaFormSchema),
    defaultValues: {
      asignado_a: '',
      descripcion: '',
      materia_id: '',
      contexto_id: '',
    },
  });

  function buildFieldClass(fieldError: string | undefined): string {
    return `w-full px-3 py-2 border rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
      fieldError ? 'border-red-500' : 'border-gray-300'
    }`;
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label
          htmlFor="tf-asignado-a"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Asignado a (UUID del usuario)
        </label>
        <input
          id="tf-asignado-a"
          type="text"
          placeholder="00000000-0000-0000-0000-000000000000"
          {...register('asignado_a')}
          className={buildFieldClass(errors.asignado_a?.message)}
        />
        {errors.asignado_a && (
          <p className="mt-1 text-xs text-red-600">
            {errors.asignado_a.message}
          </p>
        )}
      </div>

      <div>
        <label
          htmlFor="tf-descripcion"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Descripcion
        </label>
        <textarea
          id="tf-descripcion"
          rows={4}
          {...register('descripcion')}
          placeholder="Describa la tarea a realizar..."
          className={buildFieldClass(errors.descripcion?.message)}
        />
        {errors.descripcion && (
          <p className="mt-1 text-xs text-red-600">
            {errors.descripcion.message}
          </p>
        )}
      </div>

      <div>
        <label
          htmlFor="tf-materia-id"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Materia (UUID, opcional)
        </label>
        <input
          id="tf-materia-id"
          type="text"
          placeholder="UUID de la materia o dejar vacio"
          {...register('materia_id')}
          className={buildFieldClass(errors.materia_id?.message)}
        />
        {errors.materia_id && (
          <p className="mt-1 text-xs text-red-600">
            {errors.materia_id.message}
          </p>
        )}
      </div>

      <div>
        <label
          htmlFor="tf-contexto-id"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Contexto (UUID, opcional)
        </label>
        <input
          id="tf-contexto-id"
          type="text"
          placeholder="UUID de referencia contextual"
          {...register('contexto_id')}
          className={buildFieldClass(errors.contexto_id?.message)}
        />
        {errors.contexto_id && (
          <p className="mt-1 text-xs text-red-600">
            {errors.contexto_id.message}
          </p>
        )}
      </div>

      <div className="flex items-center justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" isLoading={isSubmitting}>
          {initialData ? 'Guardar cambios' : 'Crear tarea'}
        </Button>
      </div>
    </form>
  );
}

export default TareaForm;
