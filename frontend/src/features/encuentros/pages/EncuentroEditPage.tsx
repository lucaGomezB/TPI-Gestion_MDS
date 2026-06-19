import { type ReactNode } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { updateEncuentroSchema, type UpdateEncuentroFormData } from '../types/schemas';
import { useUpdateEncuentro } from '../hooks/useUpdateEncuentro';
import PageHeader from '@/shared/components/PageHeader';

const estadoOptions = ['Programado', 'Realizado', 'Cancelado'] as const;

function EncuentroEditPage(): ReactNode {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const updateEncuentro = useUpdateEncuentro();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<UpdateEncuentroFormData>({
    resolver: zodResolver(updateEncuentroSchema),
    defaultValues: {
      estado: 'Programado',
      meet_url: '',
      video_url: '',
      comentario: '',
    },
  });

  const onSubmit = (data: UpdateEncuentroFormData) => {
    if (!id) return;
    updateEncuentro.mutate(
      { id, data },
      { onSuccess: () => navigate('/encuentros') },
    );
  };

  return (
    <div>
      <PageHeader
        title="Editar encuentro"
        breadcrumbs={[
          { label: 'Encuentros', href: '/encuentros' },
          { label: 'Editar' },
        ]}
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 max-w-lg">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
          <select
            {...register('estado')}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            {estadoOptions.map((est) => (
              <option key={est} value={est}>{est}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Meet URL <span className="text-gray-400">(opcional)</span>
          </label>
          <input
            {...register('meet_url')}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            placeholder="https://meet.google.com/..."
          />
          {errors.meet_url && <p className="text-sm text-red-600 mt-1">{errors.meet_url.message}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Video URL <span className="text-gray-400">(opcional, post-evento)</span>
          </label>
          <input
            {...register('video_url')}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            placeholder="https://..."
          />
          {errors.video_url && <p className="text-sm text-red-600 mt-1">{errors.video_url.message}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Comentario <span className="text-gray-400">(opcional)</span>
          </label>
          <textarea
            {...register('comentario')}
            rows={4}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            placeholder="Comentarios sobre la clase..."
          />
          {errors.comentario && <p className="text-sm text-red-600 mt-1">{errors.comentario.message}</p>}
        </div>

        <button
          type="submit"
          disabled={updateEncuentro.isPending}
          className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {updateEncuentro.isPending ? 'Guardando...' : 'Guardar cambios'}
        </button>
      </form>
    </div>
  );
}

export default EncuentroEditPage;
