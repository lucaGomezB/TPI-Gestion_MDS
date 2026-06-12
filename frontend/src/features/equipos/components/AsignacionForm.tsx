import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { createAsignacionSchema, type CreateAsignacionData, type Asignacion } from '../types/asignaciones';
import type { Docente } from '../types/docentes';
import type { Carrera, Cohorte, Materia } from '../../estructura-academica/types/estructura';

const ROLES = ['PROFESOR', 'TUTOR', 'NEXO', 'COORDINADOR'];

interface AsignacionFormProps {
  onSubmit: (data: CreateAsignacionData) => void;
  onCancel: () => void;
  initialData?: Asignacion;
  isSubmitting?: boolean;
  docentes: Docente[];
  carreras: Carrera[];
  cohortes: Cohorte[];
  materias: Materia[];
}

function AsignacionForm({
  onSubmit,
  onCancel,
  initialData,
  isSubmitting,
  docentes,
  carreras,
  cohortes,
  materias,
}: AsignacionFormProps) {
  const {
    register,
    handleSubmit,
    control,
    watch,
    formState: { errors },
  } = useForm<CreateAsignacionData>({
    resolver: zodResolver(createAsignacionSchema),
    defaultValues: initialData
      ? {
          docente_id: initialData.docente_id,
          materia_id: initialData.materia_id,
          carrera_id: initialData.carrera_id,
          cohorte_id: initialData.cohorte_id,
          rol: initialData.rol,
          comisiones: initialData.comisiones || [],
          responsable_id: initialData.responsable_id || null,
          vig_desde: initialData.vig_desde,
          vig_hasta: initialData.vig_hasta,
        }
      : {
          docente_id: '',
          materia_id: '',
          carrera_id: '',
          cohorte_id: '',
          rol: '',
          comisiones: [],
          responsable_id: null,
          vig_desde: '',
          vig_hasta: '',
        },
  });

  const selectedCarreraId = watch('carrera_id');
  const filteredCohortes = cohortes.filter((c) => c.carrera_id === selectedCarreraId);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="docente_id" className="block text-sm font-medium text-gray-700 mb-1">
            Docente
          </label>
          <select
            id="docente_id"
            {...register('docente_id')}
            className={`w-full px-3 py-2 border rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.docente_id ? 'border-red-500' : 'border-gray-300'
            }`}
          >
            <option value="">Seleccione un docente</option>
            {docentes.map((d) => (
              <option key={d.id} value={d.id}>
                {d.nombre} {d.apellidos} - {d.email}
              </option>
            ))}
          </select>
          {errors.docente_id && (
            <p className="mt-1 text-xs text-red-600">{errors.docente_id.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="rol" className="block text-sm font-medium text-gray-700 mb-1">
            Rol
          </label>
          <select
            id="rol"
            {...register('rol')}
            className={`w-full px-3 py-2 border rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.rol ? 'border-red-500' : 'border-gray-300'
            }`}
          >
            <option value="">Seleccione un rol</option>
            {ROLES.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
          {errors.rol && (
            <p className="mt-1 text-xs text-red-600">{errors.rol.message}</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label htmlFor="carrera_id" className="block text-sm font-medium text-gray-700 mb-1">
            Carrera
          </label>
          <select
            id="carrera_id"
            {...register('carrera_id')}
            className={`w-full px-3 py-2 border rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.carrera_id ? 'border-red-500' : 'border-gray-300'
            }`}
          >
            <option value="">Seleccione</option>
            {carreras.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nombre}
              </option>
            ))}
          </select>
          {errors.carrera_id && (
            <p className="mt-1 text-xs text-red-600">{errors.carrera_id.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="materia_id" className="block text-sm font-medium text-gray-700 mb-1">
            Materia
          </label>
          <select
            id="materia_id"
            {...register('materia_id')}
            className={`w-full px-3 py-2 border rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.materia_id ? 'border-red-500' : 'border-gray-300'
            }`}
          >
            <option value="">Seleccione</option>
            {materias.map((m) => (
              <option key={m.id} value={m.id}>
                {m.nombre} ({m.codigo})
              </option>
            ))}
          </select>
          {errors.materia_id && (
            <p className="mt-1 text-xs text-red-600">{errors.materia_id.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="cohorte_id" className="block text-sm font-medium text-gray-700 mb-1">
            Cohorte
          </label>
          <select
            id="cohorte_id"
            {...register('cohorte_id')}
            className={`w-full px-3 py-2 border rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.cohorte_id ? 'border-red-500' : 'border-gray-300'
            }`}
          >
            <option value="">Seleccione</option>
            {filteredCohortes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nombre}
              </option>
            ))}
          </select>
          {errors.cohorte_id && (
            <p className="mt-1 text-xs text-red-600">{errors.cohorte_id.message}</p>
          )}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Comisiones</label>
        <Controller
          name="comisiones"
          control={control}
          render={({ field }) => (
            <div className="flex flex-wrap gap-2">
              {['A', 'B', 'C', 'D', 'E', 'F'].map((com) => (
                <label key={com} className="flex items-center space-x-1 text-sm">
                  <input
                    type="checkbox"
                    value={com}
                    checked={field.value?.includes(com) ?? false}
                    onChange={(e) => {
                      const current = field.value || [];
                      if (e.target.checked) {
                        field.onChange([...current, com]);
                      } else {
                        field.onChange(current.filter((c: string) => c !== com));
                      }
                    }}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span>Com. {com}</span>
                </label>
              ))}
            </div>
          )}
        />
      </div>

      <div>
        <label htmlFor="responsable_id" className="block text-sm font-medium text-gray-700 mb-1">
          Responsable (opcional)
        </label>
        <select
          id="responsable_id"
          {...register('responsable_id')}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Sin responsable</option>
          {docentes.map((d) => (
            <option key={d.id} value={d.id}>
              {d.nombre} {d.apellidos}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="vig_desde" className="block text-sm font-medium text-gray-700 mb-1">
            Vigencia Desde
          </label>
          <input
            id="vig_desde"
            type="date"
            {...register('vig_desde')}
            className={`w-full px-3 py-2 border rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.vig_desde ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.vig_desde && (
            <p className="mt-1 text-xs text-red-600">{errors.vig_desde.message}</p>
          )}
        </div>
        <div>
          <label htmlFor="vig_hasta" className="block text-sm font-medium text-gray-700 mb-1">
            Vigencia Hasta
          </label>
          <input
            id="vig_hasta"
            type="date"
            {...register('vig_hasta')}
            className={`w-full px-3 py-2 border rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.vig_hasta ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.vig_hasta && (
            <p className="mt-1 text-xs text-red-600">{errors.vig_hasta.message}</p>
          )}
        </div>
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

export default AsignacionForm;
