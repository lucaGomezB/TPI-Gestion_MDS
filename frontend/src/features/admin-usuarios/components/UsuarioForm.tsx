import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { UsuarioResponse } from '../types';
import { ROLES_DISPONIBLES } from '../types';
import Button from '../../../shared/components/Button';

const usuarioFormSchema = z.object({
  nombre: z.string().min(1, 'El nombre es requerido').max(100, 'Maximo 100 caracteres'),
  apellidos: z.string().min(1, 'Los apellidos son requeridos').max(200, 'Maximo 200 caracteres'),
  email: z.string().email('Email invalido').min(3).max(255),
  password: z
    .union([z.string().min(8, 'Minimo 8 caracteres').max(128), z.literal('')])
    .optional(),
  roles: z.array(z.string()).min(1, 'Seleccione al menos un rol'),
  facturador: z.boolean(),
});

export type UsuarioFormValues = z.infer<typeof usuarioFormSchema>;

interface UsuarioFormProps {
  onSubmit: (data: UsuarioFormValues) => void;
  onCancel: () => void;
  initialData?: UsuarioResponse;
  isSubmitting?: boolean;
}

function UsuarioForm({ onSubmit, onCancel, initialData, isSubmitting }: UsuarioFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<UsuarioFormValues>({
    resolver: zodResolver(usuarioFormSchema),
    defaultValues: initialData
      ? {
          nombre: initialData.nombre,
          apellidos: initialData.apellidos,
          email: initialData.email,
          password: '',
          roles: initialData.roles,
          facturador: initialData.facturador,
        }
      : {
          nombre: '',
          apellidos: '',
          email: '',
          password: '',
          roles: [],
          facturador: false,
        },
  });

  function buildFieldClass(fieldError: string | undefined): string {
    return `w-full px-3 py-2 border rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
      fieldError ? 'border-red-500' : 'border-gray-300'
    }`;
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="us-nombre" className="block text-sm font-medium text-gray-700 mb-1">
            Nombre
          </label>
          <input
            id="us-nombre"
            type="text"
            {...register('nombre')}
            className={buildFieldClass(errors.nombre?.message)}
          />
          {errors.nombre && (
            <p className="mt-1 text-xs text-red-600">{errors.nombre.message}</p>
          )}
        </div>
        <div>
          <label htmlFor="us-apellidos" className="block text-sm font-medium text-gray-700 mb-1">
            Apellidos
          </label>
          <input
            id="us-apellidos"
            type="text"
            {...register('apellidos')}
            className={buildFieldClass(errors.apellidos?.message)}
          />
          {errors.apellidos && (
            <p className="mt-1 text-xs text-red-600">{errors.apellidos.message}</p>
          )}
        </div>
      </div>

      <div>
        <label htmlFor="us-email" className="block text-sm font-medium text-gray-700 mb-1">
          Email
        </label>
        <input
          id="us-email"
          type="email"
          {...register('email')}
          className={buildFieldClass(errors.email?.message)}
        />
        {errors.email && (
          <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="us-password" className="block text-sm font-medium text-gray-700 mb-1">
          Contrasena {initialData ? '(dejar vacio para no cambiar)' : '(opcional, se autogenera)'}
        </label>
        <input
          id="us-password"
          type="password"
          {...register('password')}
          className={buildFieldClass(errors.password?.message)}
          autoComplete="new-password"
        />
        {errors.password && (
          <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Roles
        </label>
        <div className="flex flex-wrap gap-3">
          {ROLES_DISPONIBLES.map((rol) => (
            <label key={rol} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                value={rol}
                {...register('roles')}
                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-gray-700">{rol}</span>
            </label>
          ))}
        </div>
        {errors.roles && (
          <p className="mt-1 text-xs text-red-600">{errors.roles.message}</p>
        )}
      </div>

      <div className="flex items-center gap-2">
        <input
          id="us-facturador"
          type="checkbox"
          {...register('facturador')}
          className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <label htmlFor="us-facturador" className="text-sm font-medium text-gray-700">
          Facturador
        </label>
      </div>

      <div className="flex items-center justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" isLoading={isSubmitting}>
          {initialData ? 'Guardar cambios' : 'Crear usuario'}
        </Button>
      </div>
    </form>
  );
}

export default UsuarioForm;
