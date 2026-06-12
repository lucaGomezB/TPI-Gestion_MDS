import { type ReactNode } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import PageHeader from '@/shared/components/PageHeader';
import AvisoForm from '../components/AvisoForm';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import { useAviso, useCreateAviso, useUpdateAviso, useAvisosAdmin, useDeleteAviso } from '../hooks/useAvisos';
import type { AvisoFormData } from '../types';

function AvisoFormPage(): ReactNode {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEditing = !!id;

  const { data: aviso, isLoading: isLoadingAviso, isError: isErrorAviso } = useAviso(id ?? '');
  const { data: avisos, isLoading: isLoadingList } = useAvisosAdmin();
  const createMutation = useCreateAviso();
  const updateMutation = useUpdateAviso();
  const deleteMutation = useDeleteAviso();

  const handleSubmit = async (data: AvisoFormData) => {
    try {
      if (isEditing && id) {
        await updateMutation.mutateAsync({ id, data });
      } else {
        await createMutation.mutateAsync(data);
      }
      navigate('/admin/avisos');
    } catch {
      // Error handled by mutation
    }
  };

  const handleDelete = async () => {
    if (!id) return;
    try {
      await deleteMutation.mutateAsync(id);
      navigate('/admin/avisos');
    } catch {
      // Error handled by mutation
    }
  };

  if (isEditing && isLoadingAviso) return <Loading skeleton />;
  if (isEditing && isErrorAviso) return <ErrorDisplay message="Error al cargar aviso" />;

  return (
    <div>
      <PageHeader
        title={isEditing ? 'Editar aviso' : 'Nuevo aviso'}
        breadcrumbs={[
          { label: 'Admin Avisos', href: '/admin/avisos' },
          { label: isEditing ? 'Editar' : 'Nuevo' },
        ]}
      />

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <AvisoForm
          onSubmit={handleSubmit}
          isSubmitting={createMutation.isPending || updateMutation.isPending}
          initialData={isEditing ? aviso : undefined}
        />

        {isEditing && (
          <div className="mt-8 pt-6 border-t border-gray-200">
            <button
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              className="px-4 py-2 text-sm font-medium text-red-700 bg-white border border-red-300 rounded-md hover:bg-red-50 disabled:opacity-50 transition-colors"
            >
              {deleteMutation.isPending ? 'Eliminando...' : 'Eliminar aviso'}
            </button>
          </div>
        )}
      </div>

      {/* Lista de avisos existentes */}
      <div className="mt-8">
        <div className="bg-white border border-gray-200 rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Avisos existentes</h2>
          </div>
          {isLoadingList ? (
            <Loading skeleton />
          ) : !avisos || avisos.length === 0 ? (
            <div className="p-6 text-sm text-gray-500 text-center">No hay avisos creados.</div>
          ) : (
            <div className="divide-y divide-gray-200">
              {avisos.map((a) => (
                <div
                  key={a.id}
                  className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/admin/avisos/${a.id}/editar`)}
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900">{a.titulo}</p>
                    <p className="text-xs text-gray-500">
                      {a.alcance} · {a.severidad} · {new Date(a.inicio_vigencia).toLocaleDateString('es-AR')} → {new Date(a.fin_vigencia).toLocaleDateString('es-AR')}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AvisoFormPage;
