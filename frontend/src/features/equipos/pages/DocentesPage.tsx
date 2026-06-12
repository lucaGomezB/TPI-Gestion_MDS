import { useState, type ReactNode } from 'react';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';
import DocenteForm from '../components/DocenteForm';
import { useDocentes, useCreateDocente, useUpdateDocente } from '../hooks/useEquipos';
import type { Docente, CreateDocenteData, UpdateDocenteData } from '../types/docentes';

function DocentesPage(): ReactNode {
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState<Docente | null>(null);

  const { data: docentes, isLoading, error, refetch } = useDocentes();
  const createMutation = useCreateDocente();
  const updateMutation = useUpdateDocente();

  const handleCreate = async (data: CreateDocenteData) => {
    try {
      await createMutation.mutateAsync(data);
      setShowForm(false);
    } catch {
      // Error handled by query client
    }
  };

  const handleUpdate = async (data: CreateDocenteData) => {
    if (!editingItem?.id) return;
    try {
      await updateMutation.mutateAsync({ id: editingItem.id, data: data as UpdateDocenteData });
      setEditingItem(null);
    } catch {
      // Error handled by query client
    }
  };

  const handleToggle = async (item: Docente) => {
    if (!item.id) return;
    try {
      await updateMutation.mutateAsync({
        id: item.id,
        data: {
          nombre: item.nombre,
          apellidos: item.apellidos,
          email: item.email,
          roles: item.roles,
          regional: item.regional || '',
          activo: !item.activo,
        },
      });
    } catch {
      // Error handled by query client
    }
  };

  if (isLoading) return <Loading />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  return (
    <div>
      <PageHeader
        title="Docentes"
        breadcrumbs={[{ label: 'Administración' }, { label: 'Equipos' }, { label: 'Docentes' }]}
        actions={
          !showForm && !editingItem
            ? [{ label: 'Nuevo Docente', onClick: () => setShowForm(true) }]
            : undefined
        }
      />

      {showForm && (
        <div className="mb-6 p-4 bg-white rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Nuevo Docente</h3>
          <DocenteForm
            onSubmit={handleCreate}
            onCancel={() => setShowForm(false)}
            isSubmitting={createMutation.isPending}
          />
        </div>
      )}

      {editingItem && (
        <div className="mb-6 p-4 bg-white rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Editar Docente: {editingItem.nombre} {editingItem.apellidos}
          </h3>
          <DocenteForm
            onSubmit={handleUpdate}
            onCancel={() => setEditingItem(null)}
            initialData={editingItem}
            isSubmitting={updateMutation.isPending}
          />
        </div>
      )}

      {!docentes || docentes.length === 0 ? (
        <EmptyState
          title="No hay docentes"
          description="Cargue el primer docente para comenzar."
          actionLabel="Nuevo Docente"
          onAction={() => setShowForm(true)}
        />
      ) : (
        <div className="overflow-x-auto bg-white rounded-lg shadow-sm border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Nombre</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Apellidos</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Email</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Regional</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Roles</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {docentes.map((doc) => (
                <tr key={doc.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 text-sm text-gray-700">{doc.nombre}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{doc.apellidos}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{doc.email}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{doc.regional || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">
                    {doc.roles.join(', ')}
                  </td>
                  <td className="px-4 py-3 text-right text-sm">
                    <div className="flex items-center justify-end space-x-2">
                      <button
                        onClick={() => handleToggle(doc)}
                        className={`px-2 py-1 text-xs font-medium rounded-full transition-colors ${
                          doc.activo
                            ? 'bg-green-100 text-green-700 hover:bg-green-200'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        {doc.activo ? 'Activo' : 'Inactivo'}
                      </button>
                      <button
                        onClick={() => setEditingItem(doc)}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium transition-colors"
                      >
                        Editar
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default DocentesPage;
