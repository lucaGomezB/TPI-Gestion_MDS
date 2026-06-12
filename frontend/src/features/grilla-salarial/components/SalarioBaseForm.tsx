import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { SalarioBase, SalarioBaseCreate, SalarioBaseUpdate } from '../types';
import { ROLES_SALARIALES } from '../types';

const salarioBaseSchema = z.object({
  rol: z.string().min(1, 'Seleccione un rol'),
  monto: z.coerce.number().positive('El monto debe ser positivo'),
  desde: z.string().min(1, 'Fecha desde requerida'),
  hasta: z.string().nullable().optional(),
});

type SalarioBaseFormData = z.infer<typeof salarioBaseSchema>;

interface SalarioBaseFormProps {
  initialData?: SalarioBase;
  onSubmit: (data: SalarioBaseCreate | SalarioBaseUpdate) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
}

function SalarioBaseForm({ initialData, onSubmit, onCancel, isSubmitting }: SalarioBaseFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SalarioBaseFormData>({
    resolver: zodResolver(salarioBaseSchema),
    defaultValues: initialData
      ? {
          rol: initialData.rol,
          monto: initialData.monto,
          desde: initialData.desde,
          hasta: initialData.hasta,
        }
      : {
          rol: '',
          monto: undefined as unknown as number,
          desde: '',
          hasta: null,
        },
  });

  const handleFormSubmit = (data: SalarioBaseFormData) => {
    const payload = initialData
      ? (data as SalarioBaseUpdate)
      : (data as SalarioBaseCreate);
    void onSubmit(payload);
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <div>
        <label htmlFor="rol" className="block text-sm font-medium text-gray-700">
          Rol
        </label>
        <select
          id="rol"
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
        <label htmlFor="monto" className="block text-sm font-medium text-gray-700">
          Monto
        </label>
        <input
          id="monto"
          type="number"
          step="0.01"
          {...register('monto')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        {errors.monto && <p className="mt-1 text-sm text-red-600">{errors.monto.message}</p>}
      </div>

      <div>
        <label htmlFor="desde" className="block text-sm font-medium text-gray-700">
          Vigencia desde
        </label>
        <input
          id="desde"
          type="date"
          {...register('desde')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        {errors.desde && <p className="mt-1 text-sm text-red-600">{errors.desde.message}</p>}
      </div>

      <div>
        <label htmlFor="hasta" className="block text-sm font-medium text-gray-700">
          Vigencia hasta (opcional)
        </label>
        <input
          id="hasta"
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

export default SalarioBaseForm;
