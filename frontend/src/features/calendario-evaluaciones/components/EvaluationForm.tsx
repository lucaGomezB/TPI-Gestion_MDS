import { useEffect, type ReactNode } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { evaluationDateSchema, tipoEvaluacionEnum } from '../types';
import Modal from '@/shared/components/Modal';
import type { EvaluationDate } from '../types';

// --- Task 4.4: EvaluationForm modal ---

interface SelectOption {
  value: string;
  label: string;
}

interface EvaluationFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: EvaluationFormData) => void;
  initialData?: EvaluationDate;
  materias: SelectOption[];
  cohortes: SelectOption[];
  isSubmitting?: boolean;
}

const formSchema = evaluationDateSchema.omit({ id: true });
type EvaluationFormData = z.infer<typeof formSchema>;

function EvaluationForm({
  isOpen,
  onClose,
  onSubmit,
  initialData,
  materias,
  cohortes,
  isSubmitting = false,
}: EvaluationFormProps): ReactNode {
  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<EvaluationFormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      materia_id: '',
      cohorte_id: '',
      tipo: 'Parcial',
      numero_instancia: 1,
      fecha: '',
      titulo: '',
    },
  });

  // Populate form when editing
  useEffect(() => {
    if (initialData) {
      reset({
        materia_id: initialData.materia_id,
        cohorte_id: initialData.cohorte_id,
        tipo: initialData.tipo,
        numero_instancia: initialData.numero_instancia,
        fecha: initialData.fecha,
        titulo: initialData.titulo,
      });
    } else {
      reset({
        materia_id: '',
        cohorte_id: '',
        tipo: 'Parcial',
        numero_instancia: 1,
        fecha: '',
        titulo: '',
      });
    }
  }, [initialData, reset, isOpen]);

  const selectedMateria = watch('materia_id');
  const filteredCohortes = selectedMateria
    ? cohortes
    : cohortes;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={initialData ? 'Editar Evaluacion' : 'Nueva Evaluacion'}
      size="md"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {/* Materia */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Materia</label>
          <select
            {...register('materia_id')}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">Seleccione una materia</option>
            {materias.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          {errors.materia_id && (
            <p className="text-sm text-red-600 mt-1">{errors.materia_id.message}</p>
          )}
        </div>

        {/* Cohorte */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Cohorte</label>
          <select
            {...register('cohorte_id')}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">Seleccione un cohorte</option>
            {filteredCohortes.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          {errors.cohorte_id && (
            <p className="text-sm text-red-600 mt-1">{errors.cohorte_id.message}</p>
          )}
        </div>

        {/* Tipo */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
          <select
            {...register('tipo')}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            {tipoEvaluacionEnum.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          {errors.tipo && (
            <p className="text-sm text-red-600 mt-1">{errors.tipo.message}</p>
          )}
        </div>

        {/* Numero de instancia */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Instancia Nro</label>
          <input
            type="number"
            {...register('numero_instancia', { valueAsNumber: true })}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            min={1}
          />
          {errors.numero_instancia && (
            <p className="text-sm text-red-600 mt-1">{errors.numero_instancia.message}</p>
          )}
        </div>

        {/* Fecha */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Fecha</label>
          <input
            type="date"
            {...register('fecha')}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          />
          {errors.fecha && (
            <p className="text-sm text-red-600 mt-1">{errors.fecha.message}</p>
          )}
        </div>

        {/* Titulo */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Titulo</label>
          <input
            type="text"
            {...register('titulo')}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            placeholder="Ej: Primer parcial"
          />
          {errors.titulo && (
            <p className="text-sm text-red-600 mt-1">{errors.titulo.message}</p>
          )}
        </div>

        {/* Actions */}
        <div className="flex justify-end space-x-3 pt-2">
          <button
            type="button"
            onClick={onClose}
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
    </Modal>
  );
}

export default EvaluationForm;
