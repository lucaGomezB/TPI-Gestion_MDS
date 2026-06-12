import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { createMateriaSchema, type CreateMateriaData, type Materia } from '../types/estructura';

interface MateriaFormProps {
  onSubmit: (data: CreateMateriaData) => void;
  onCancel: () => void;
  initialData?: Materia;
  isSubmitting?: boolean;
}

function MateriaForm({ onSubmit, onCancel, initialData, isSubmitting }: MateriaFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CreateMateriaData>({
    resolver: zodResolver(createMateriaSchema),
    defaultValues: initialData
      ? { codigo: initialData.codigo, nombre: initialData.nombre }
      : { codigo: '', nombre: '' },
  });

  const isEditing = !!initialData;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="codigo" className="block text-sm font-medium text-gray-700 mb-1">
          Código
        </label>
        <input
          id="codigo"
          type="text"
          {...register('codigo')}
          readOnly={isEditing}
          className={`w-full px-3 py-2 border rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
            isEditing
              ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
              : 'border-gray-300'
          } ${errors.codigo ? 'border-red-500' : ''}`}
          placeholder="Ej: MAT-101"
        />
        {errors.codigo && (
          <p className="mt-1 text-xs text-red-600">{errors.codigo.message}</p>
        )}
      </div>

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
          placeholder="Ej: Matemática I"
        />
        {errors.nombre && (
          <p className="mt-1 text-xs text-red-600">{errors.nombre.message}</p>
        )}
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
          {isSubmitting ? 'Guardando...' : isEditing ? 'Actualizar' : 'Crear'}
        </button>
      </div>
    </form>
  );
}

export default MateriaForm;
