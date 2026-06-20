import { useState, type ReactNode } from 'react';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';
import DataTable from '../components/DataTable';
import CarreraForm from '../components/CarreraForm';
import { useCarreras, useCreateCarrera, useUpdateCarrera } from '../hooks/useCarreras';
import type { Carrera, CreateCarreraData } from '../types/estructura';

function CarrerasPage(): ReactNode {
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState<Carrera | null>(null);

  const { data: carreras, isLoading, error, refetch } = useCarreras();
  const createMutation = useCreateCarrera();
  const updateMutation = useUpdateCarrera();

  const handleCreate = async (data: CreateCarreraData) => {
    try {
      await createMutation.mutateAsync(data);
      setShowForm(false);
    } catch {
      // Error handled by query client
    }
  };

  const handleUpdate = async (data: CreateCarreraData) => {
    if (!editingItem?.id) return;
    try {
      await updateMutation.mutateAsync({ id: editingItem.id, data: { nombre: data.nombre, estado: editingItem.estado } });
      setEditingItem(null);
    } catch {
      // Error handled by query client
    }
  };

  const handleToggle = async (item: Carrera) => {
    if (!item.id) return;
    try {
      await updateMutation.mutateAsync({
        id: item.id,
        data: { nombre: item.nombre, estado: item.estado === 'Activa' ? 'Inactiva' : 'Activa' },
      });
    } catch {
      // Error handled by query client
    }
  };

  const columns = [
    { key: 'codigo', header: 'Código' },
    { key: 'nombre', header: 'Nombre' },
  ];

  if (isLoading) return <Loading />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  return (
    <div>
      <PageHeader
        title="Carreras"
        breadcrumbs={[{ label: 'Administración' }, { label: 'Carreras' }]}
        actions={
          !showForm && !editingItem
            ? [{ label: 'Nueva Carrera', onClick: () => setShowForm(true) }]
            : undefined
        }
      />

      {showForm && (
        <div className="mb-6 p-4 bg-white rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Nueva Carrera</h3>
          <CarreraForm
            onSubmit={handleCreate}
            onCancel={() => setShowForm(false)}
            isSubmitting={createMutation.isPending}
          />
        </div>
      )}

      {editingItem && (
        <div className="mb-6 p-4 bg-white rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Editar Carrera: {editingItem.codigo}
          </h3>
          <CarreraForm
            onSubmit={handleUpdate}
            onCancel={() => setEditingItem(null)}
            initialData={editingItem}
            isSubmitting={updateMutation.isPending}
          />
        </div>
      )}

      {!carreras || carreras.length === 0 ? (
        <EmptyState
          title="No hay carreras"
          description="Cree la primera carrera para comenzar."
          actionLabel="Nueva Carrera"
          onAction={() => setShowForm(true)}
        />
      ) : (
        <DataTable<Carrera>
          columns={columns}
          data={carreras}
          keyExtractor={(item) => item.id ?? item.codigo}
          onEdit={(item) => setEditingItem(item)}
          onToggle={handleToggle}
          toggleLabel={(item) => item.estado}
          toggleActive={(item) => item.estado === 'Activa'}
        />
      )}
    </div>
  );
}

export default CarrerasPage;
