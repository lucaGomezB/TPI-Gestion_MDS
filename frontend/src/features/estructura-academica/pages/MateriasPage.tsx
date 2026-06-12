import { useState, type ReactNode } from 'react';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';
import DataTable from '../components/DataTable';
import MateriaForm from '../components/MateriaForm';
import ProgramaUploader from '../components/ProgramaUploader';
import { useMaterias, useCreateMateria, useUpdateMateria } from '../hooks/useMaterias';
import { useCarreras } from '../hooks/useCarreras';
import { useCohortes } from '../hooks/useCohortes';
import type { Materia, CreateMateriaData } from '../types/estructura';

function MateriasPage(): ReactNode {
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState<Materia | null>(null);
  const [selectedMateria, setSelectedMateria] = useState<Materia | null>(null);

  const { data: materias, isLoading, error, refetch } = useMaterias();
  const { data: carreras } = useCarreras();
  const { data: cohortes } = useCohortes();
  const createMutation = useCreateMateria();
  const updateMutation = useUpdateMateria();

  const handleCreate = async (data: CreateMateriaData) => {
    try {
      await createMutation.mutateAsync(data);
      setShowForm(false);
    } catch {
      // Error handled by query client
    }
  };

  const handleUpdate = async (data: CreateMateriaData) => {
    if (!editingItem?.id) return;
    try {
      await updateMutation.mutateAsync({ id: editingItem.id, data });
      setEditingItem(null);
    } catch {
      // Error handled by query client
    }
  };

  const handleToggle = async (item: Materia) => {
    if (!item.id) return;
    try {
      await updateMutation.mutateAsync({
        id: item.id,
        data: { nombre: item.nombre, activo: !item.activo },
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
        title="Materias"
        breadcrumbs={[{ label: 'Administración' }, { label: 'Materias' }]}
        actions={
          !showForm && !editingItem
            ? [{ label: 'Nueva Materia', onClick: () => setShowForm(true) }]
            : undefined
        }
      />

      {showForm && (
        <div className="mb-6 p-4 bg-white rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Nueva Materia</h3>
          <MateriaForm
            onSubmit={handleCreate}
            onCancel={() => setShowForm(false)}
            isSubmitting={createMutation.isPending}
          />
        </div>
      )}

      {editingItem && (
        <div className="mb-6 p-4 bg-white rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Editar Materia: {editingItem.codigo}
          </h3>
          <MateriaForm
            onSubmit={handleUpdate}
            onCancel={() => setEditingItem(null)}
            initialData={editingItem}
            isSubmitting={updateMutation.isPending}
          />
        </div>
      )}

      {!materias || materias.length === 0 ? (
        <EmptyState
          title="No hay materias"
          description="Cree la primera materia para comenzar."
          actionLabel="Nueva Materia"
          onAction={() => setShowForm(true)}
        />
      ) : (
        <>
          <DataTable<Materia>
            columns={columns}
            data={materias}
            keyExtractor={(item) => item.id ?? item.codigo}
            onEdit={(item) => setEditingItem(item)}
            onToggle={handleToggle}
            toggleLabel={(item) => (item.activo ? 'Activa' : 'Inactiva')}
            toggleActive={(item) => !!item.activo}
            actions={(item) => (
              <button
                onClick={() =>
                  setSelectedMateria(
                    selectedMateria?.id === item.id ? null : item,
                  )
                }
                className={`px-2 py-1 text-xs font-medium rounded transition-colors ${
                  selectedMateria?.id === item.id
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                Programa
              </button>
            )}
          />

          {selectedMateria && carreras && cohortes && (
            <ProgramaUploader
              materiaId={selectedMateria.id ?? ''}
              materiaNombre={selectedMateria.nombre}
              carreras={carreras}
              cohortes={cohortes}
            />
          )}
        </>
      )}
    </div>
  );
}

export default MateriasPage;
