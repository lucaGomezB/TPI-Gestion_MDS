import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  createDocenteSchema,
  type CreateDocenteData,
  type Docente,
  DOCENTE_ROLES,
  REGIONALES,
} from '../types/docentes';

interface DocenteFormProps {
  onSubmit: (data: CreateDocenteData) => void;
  onCancel: () => void;
  initialData?: Docente;
  isSubmitting?: boolean;
}

function DocenteForm({ onSubmit, onCancel, initialData, isSubmitting }: DocenteFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CreateDocenteData>({
    resolver: zodResolver(createDocenteSchema),
    defaultValues: initialData
      ? {
          nombre: initialData.nombre,
          apellidos: initialData.apellidos,
          email: initialData.email,
          roles: initialData.roles,
          regional: initialData.regional || '',
        }
      : {
          nombre: '',
          apellidos: '',
          email: '',
          roles: [],
          regional: '',
        },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
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
          />
          {errors.nombre && (
            <p className="mt-1 text-xs text-red-600">{errors.nombre.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="apellidos" className="block text-sm font-medium text-gray-700 mb-1">
            Apellidos
          </label>
          <input
            id="apellidos"
            type="text"
            {...register('apellidos')}
            className={`w-full px-3 py-2 border rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.apellidos ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.apellidos && (
            <p className="mt-1 text-xs text-red-600">{errors.apellidos.message}</p>
          )}
        </div>
      </div>

      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
          Email
        </label>
        <input
          id="email"
          type="email"
          {...register('email')}
          className={`w-full px-3 py-2 border rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
            errors.email ? 'border-red-500' : 'border-gray-300'
          }`}
        />
        {errors.email && (
          <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Roles</label>
        <div className="flex flex-wrap gap-3">
          {DOCENTE_ROLES.map((rol) => (
            <label key={rol.value} className="flex items-center space-x-2 text-sm">
              <input
                type="checkbox"
                value={rol.value}
                {...register('roles')}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span>{rol.label}</span>
            </label>
          ))}
        </div>
        {errors.roles && (
          <p className="mt-1 text-xs text-red-600">{errors.roles.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="regional" className="block text-sm font-medium text-gray-700 mb-1">
          Regional
        </label>
        <select
          id="regional"
          {...register('regional')}
          className={`w-full px-3 py-2 border rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
            errors.regional ? 'border-red-500' : 'border-gray-300'
          }`}
        >
          <option value="">Seleccione una regional</option>
          {REGIONALES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
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

export default DocenteForm;
