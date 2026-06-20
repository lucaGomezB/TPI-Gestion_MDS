import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { RolResponse, ModuloPermisos } from '../types';
import Button from '../../../shared/components/Button';

const rolFormSchema = z.object({
  nombre: z.string().min(1, 'El nombre es requerido').max(50, 'Maximo 50 caracteres'),
  descripcion: z.string().max(255, 'Maximo 255 caracteres').optional().default(''),
  permisos: z.array(z.string()),
});

export type RolFormValues = z.infer<typeof rolFormSchema>;

interface RolFormProps {
  onSubmit: (data: RolFormValues) => void;
  onCancel: () => void;
  initialData?: RolResponse;
  modulosPermisos: ModuloPermisos[];
  isSubmitting?: boolean;
}

function RolForm({
  onSubmit,
  onCancel,
  initialData,
  modulosPermisos,
  isSubmitting,
}: RolFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RolFormValues>({
    resolver: zodResolver(rolFormSchema),
    defaultValues: initialData
      ? {
          nombre: initialData.nombre,
          descripcion: initialData.descripcion ?? '',
          permisos: initialData.permisos,
        }
      : {
          nombre: '',
          descripcion: '',
          permisos: [],
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
        <label htmlFor="rol-nombre" className="block text-sm font-medium text-gray-700 mb-1">
          Nombre del rol
        </label>
        <input
          id="rol-nombre"
          type="text"
          {...register('nombre')}
          className={buildFieldClass(errors.nombre?.message)}
          placeholder="Ej: EDITOR_INVITADO"
        />
        {errors.nombre && (
          <p className="mt-1 text-xs text-red-600">{errors.nombre.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="rol-descripcion" className="block text-sm font-medium text-gray-700 mb-1">
          Descripcion
        </label>
        <input
          id="rol-descripcion"
          type="text"
          {...register('descripcion')}
          className={buildFieldClass(errors.descripcion?.message)}
          placeholder="Descripcion opcional del rol"
        />
        {errors.descripcion && (
          <p className="mt-1 text-xs text-red-600">{errors.descripcion.message}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Permisos
        </label>
        {modulosPermisos.length === 0 ? (
          <p className="text-gray-400 text-xs">Cargando permisos disponibles...</p>
        ) : (
          <div className="border border-gray-200 rounded-md divide-y divide-gray-100 max-h-64 overflow-y-auto">
            {modulosPermisos.map((modulo) => (
              <div key={modulo.modulo} className="px-3 py-2">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                  {modulo.modulo}
                </p>
                <div className="flex flex-wrap gap-x-4 gap-y-1">
                  {modulo.permisos.map((perm) => {
                    const accion = perm.split(':')[1] ?? perm;
                    return (
                      <label
                        key={perm}
                        className="flex items-center gap-1.5 text-sm cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          value={perm}
                          {...register('permisos')}
                          className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-gray-700">{accion}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
        {errors.permisos && (
          <p className="mt-1 text-xs text-red-600">{errors.permisos.message}</p>
        )}
      </div>

      <div className="flex items-center justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" isLoading={isSubmitting}>
          {initialData ? 'Guardar cambios' : 'Crear rol'}
        </Button>
      </div>
    </form>
  );
}

export default RolForm;
