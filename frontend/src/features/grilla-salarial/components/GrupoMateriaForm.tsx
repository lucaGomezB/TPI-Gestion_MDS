import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { GrupoMateria, GrupoMateriaCreate, GrupoMateriaUpdate } from '../types';

const grupoMateriaSchema = z.object({
  grupo: z.string().min(1, 'El nombre del grupo es requerido').max(20),
  descripcion: z.string().max(255).nullable().optional(),
});

type GrupoMateriaFormData = z.infer<typeof grupoMateriaSchema>;

interface GrupoMateriaFormProps {
  initialData?: GrupoMateria;
  onSubmit: (data: GrupoMateriaCreate | GrupoMateriaUpdate) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
}

function GrupoMateriaForm({ initialData, onSubmit, onCancel, isSubmitting }: GrupoMateriaFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<GrupoMateriaFormData>({
    resolver: zodResolver(grupoMateriaSchema),
    defaultValues: initialData
      ? {
          grupo: initialData.grupo,
          descripcion: initialData.descripcion,
        }
      : {
          grupo: '',
          descripcion: null,
        },
  });

  const handleFormSubmit = (data: GrupoMateriaFormData) => {
    const payload = initialData
      ? (data as GrupoMateriaUpdate)
      : (data as GrupoMateriaCreate);
    void onSubmit(payload);
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <div>
        <label htmlFor="grupo-nombre" className="block text-sm font-medium text-gray-700">
          Nombre del grupo
        </label>
        <input
          id="grupo-nombre"
          {...register('grupo')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        {errors.grupo && <p className="mt-1 text-sm text-red-600">{errors.grupo.message}</p>}
      </div>

      <div>
        <label htmlFor="grupo-descripcion" className="block text-sm font-medium text-gray-700">
          Descripcion (opcional)
        </label>
        <input
          id="grupo-descripcion"
          {...register('descripcion')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </div>

      <div className="flex justify-end space-x-3 pt-2">
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
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {isSubmitting ? 'Guardando...' : initialData ? 'Actualizar' : 'Crear'}
        </button>
      </div>
    </form>
  );
}

export default GrupoMateriaForm;
