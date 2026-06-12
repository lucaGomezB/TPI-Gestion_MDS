import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { SalarioPlus, SalarioPlusCreate, SalarioPlusUpdate } from '../types';
import { ROLES_SALARIALES } from '../types';

const salarioPlusSchema = z.object({
  grupo: z.string().min(1, 'El grupo es requerido').max(50),
  rol: z.string().min(1, 'Seleccione un rol'),
  descripcion: z.string().min(1, 'La descripcion es requerida').max(255),
  monto: z.coerce.number().positive('El monto debe ser positivo'),
  desde: z.string().min(1, 'Fecha desde requerida'),
  hasta: z.string().nullable().optional(),
});

type SalarioPlusFormData = z.infer<typeof salarioPlusSchema>;

interface SalarioPlusFormProps {
  initialData?: SalarioPlus;
  onSubmit: (data: SalarioPlusCreate | SalarioPlusUpdate) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
}

function SalarioPlusForm({ initialData, onSubmit, onCancel, isSubmitting }: SalarioPlusFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SalarioPlusFormData>({
    resolver: zodResolver(salarioPlusSchema),
    defaultValues: initialData
      ? {
          grupo: initialData.grupo,
          rol: initialData.rol,
          descripcion: initialData.descripcion,
          monto: initialData.monto,
          desde: initialData.desde,
          hasta: initialData.hasta,
        }
      : {
          grupo: '',
          rol: '',
          descripcion: '',
          monto: undefined as unknown as number,
          desde: '',
          hasta: null,
        },
  });

  const handleFormSubmit = (data: SalarioPlusFormData) => {
    const payload = initialData
      ? (data as SalarioPlusUpdate)
      : (data as SalarioPlusCreate);
    void onSubmit(payload);
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <div>
        <label htmlFor="plus-grupo" className="block text-sm font-medium text-gray-700">
          Grupo
        </label>
        <input
          id="plus-grupo"
          {...register('grupo')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        {errors.grupo && <p className="mt-1 text-sm text-red-600">{errors.grupo.message}</p>}
      </div>

      <div>
        <label htmlFor="plus-rol" className="block text-sm font-medium text-gray-700">
          Rol
        </label>
        <select
          id="plus-rol"
          {...register('rol')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">Seleccione...</option>
          {ROLES_SALARIALES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
        {errors.rol && <p className="mt-1 text-sm text-red-600">{errors.rol.message}</p>}
      </div>

      <div>
        <label htmlFor="plus-descripcion" className="block text-sm font-medium text-gray-700">
          Descripcion
        </label>
        <input
          id="plus-descripcion"
          {...register('descripcion')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        {errors.descripcion && <p className="mt-1 text-sm text-red-600">{errors.descripcion.message}</p>}
      </div>

      <div>
        <label htmlFor="plus-monto" className="block text-sm font-medium text-gray-700">
          Monto
        </label>
        <input
          id="plus-monto"
          type="number"
          step="0.01"
          {...register('monto')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        {errors.monto && <p className="mt-1 text-sm text-red-600">{errors.monto.message}</p>}
      </div>

      <div>
        <label htmlFor="plus-desde" className="block text-sm font-medium text-gray-700">
          Vigencia desde
        </label>
        <input
          id="plus-desde"
          type="date"
          {...register('desde')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        {errors.desde && <p className="mt-1 text-sm text-red-600">{errors.desde.message}</p>}
      </div>

      <div>
        <label htmlFor="plus-hasta" className="block text-sm font-medium text-gray-700">
          Vigencia hasta (opcional)
        </label>
        <input
          id="plus-hasta"
          type="date"
          {...register('hasta')}
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

export default SalarioPlusForm;
