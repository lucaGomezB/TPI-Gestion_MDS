import { useState, type ReactNode } from 'react';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';
import DataTable from '../components/DataTable';
import CohorteForm from '../components/CohorteForm';
import { useCarreras } from '../hooks/useCarreras';
import { useCohortes, useCreateCohorte, useUpdateCohorte } from '../hooks/useCohortes';
import type { Cohorte, CreateCohorteData } from '../types/estructura';

function CohortesPage(): ReactNode {
  const [selectedCarreraId, setSelectedCarreraId] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState<Cohorte | null>(null);

  const { data: carreras, isLoading: loadingCarreras } = useCarreras();
  const { data: cohortes, isLoading, error, refetch } = useCohortes(selectedCarreraId || undefined);
  const createMutation = useCreateCohorte();
  const updateMutation = useUpdateCohorte();

  const handleCreate = async (data: CreateCohorteData) => {
    try {
      await createMutation.mutateAsync(data);
      setShowForm(false);
    } catch {
      // Error handled by query client
    }
  };

  const handleUpdate = async (data: CreateCohorteData) => {
    if (!editingItem?.id) return;
    try {
      await updateMutation.mutateAsync({ id: editingItem.id, data: { ...data, estado: editingItem.estado } });
      setEditingItem(null);
    } catch {
      // Error handled by query client
    }
  };

  const handleToggle = async (item: Cohorte) => {
    if (!item.id) return;
    try {
      await updateMutation.mutateAsync({
        id: item.id,
        data: { ...item, estado: item.estado === 'Activa' ? 'Inactiva' : 'Activa' },
      });
    } catch {
      // Error handled by query client
    }
  };

  const columns = [
    { key: 'nombre', header: 'Nombre' },
    { key: 'anio_inicio', header: 'Año Inicio' },
    {
      key: 'vig_desde',
      header: 'Vig. Desde',
      render: (item: Cohorte) => item.vig_desde || '-',
    },
    {
      key: 'vig_hasta',
      header: 'Vig. Hasta',
      render: (item: Cohorte) => item.vig_hasta || '-',
    },
  ];

  // Get selected carrera name for the form
  const carrerasList = carreras || [];

  return (
    <div>
      <PageHeader
        title="Cohortes"
        breadcrumbs={[{ label: 'Administración' }, { label: 'Cohortes' }]}
      />

      {/* Carrera filter */}
      <div className="mb-4">
        <label htmlFor="carrera-filter" className="block text-sm font-medium text-gray-700 mb-1">
          Filtrar por Carrera
        </label>
        <select
          id="carrera-filter"
          value={selectedCarreraId}
          onChange={(e) => {
            setSelectedCarreraId(e.target.value);
            setShowForm(false);
            setEditingItem(null);
          }}
          className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-md text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Seleccione una carrera</option>
          {carrerasList.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre} ({c.codigo})
            </option>
          ))}
        </select>
      </div>

      {!selectedCarreraId ? (
        <EmptyState
          title="Seleccione una carrera"
          description="Use el filtro superior para ver las cohortes de una carrera."
        />
      ) : loadingCarreras || isLoading ? (
        <Loading />
      ) : error ? (
        <ErrorDisplay onRetry={refetch} />
      ) : (
        <>
          <div className="flex justify-end mb-4">
            {!showForm && !editingItem && (
              <button
                onClick={() => setShowForm(true)}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
              >
                Nueva Cohorte
              </button>
            )}
          </div>

          {showForm && (
            <div className="mb-6 p-4 bg-white rounded-lg shadow-sm border border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Nueva Cohorte</h3>
              <CohorteForm
                onSubmit={handleCreate}
                onCancel={() => setShowForm(false)}
                isSubmitting={createMutation.isPending}
                carreras={carrerasList}
              />
            </div>
          )}

          {editingItem && (
            <div className="mb-6 p-4 bg-white rounded-lg shadow-sm border border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">
                Editar Cohorte: {editingItem.nombre}
              </h3>
              <CohorteForm
                onSubmit={handleUpdate}
                onCancel={() => setEditingItem(null)}
                initialData={editingItem}
                isSubmitting={updateMutation.isPending}
                carreras={carrerasList}
              />
            </div>
          )}

          {!cohortes || cohortes.length === 0 ? (
            <EmptyState
              title="No hay cohortes"
              description="No se encontraron cohortes para la carrera seleccionada."
              actionLabel="Nueva Cohorte"
              onAction={() => setShowForm(true)}
            />
          ) : (
            <DataTable<Cohorte>
              columns={columns}
              data={cohortes}
              keyExtractor={(item) => item.id ?? ''}
              onEdit={(item) => setEditingItem(item)}
              onToggle={handleToggle}
              toggleLabel={(item) => item.estado}
              toggleActive={(item) => item.estado === 'Activa'}
            />
          )}
        </>
      )}
    </div>
  );
}

export default CohortesPage;
