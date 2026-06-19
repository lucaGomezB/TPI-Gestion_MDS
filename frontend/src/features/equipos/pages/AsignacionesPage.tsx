import { useState, type ReactNode } from 'react';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';
import AsignacionForm from '../components/AsignacionForm';
import AsignacionTable from '../components/AsignacionTable';
import { useAsignaciones, useCreateAsignacion, useUpdateAsignacion } from '../hooks/useAsignaciones';
import { useDocentes } from '../hooks/useEquipos';
import { useCarreras } from '../../estructura-academica/hooks/useCarreras';
import { useCohortes } from '../../estructura-academica/hooks/useCohortes';
import { useMaterias } from '../../estructura-academica/hooks/useMaterias';
import type { AsignacionDisplay, AsignacionFilters, CreateAsignacionData } from '../types/asignaciones';
import { Link } from 'react-router-dom';

function AsignacionesPage(): ReactNode {
  const [filters, setFilters] = useState<AsignacionFilters>({});
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState<AsignacionDisplay | null>(null);

  const { data: asignaciones, isLoading, error, refetch } = useAsignaciones(filters);
  const { data: docentes = [] } = useDocentes();
  const { data: carreras = [] } = useCarreras();
  const { data: cohortes = [] } = useCohortes();
  const { data: materias = [] } = useMaterias();
  const createMutation = useCreateAsignacion();
  const updateMutation = useUpdateAsignacion();

  const handleCreate = async (data: CreateAsignacionData) => {
    try {
      await createMutation.mutateAsync(data);
      setShowForm(false);
    } catch {
      // Error handled by query client
    }
  };

  const handleToggle = async (item: AsignacionDisplay) => {
    // Toggle via update - uses the display item to create update data
    try {
      await updateMutation.mutateAsync({
        id: item.id,
        data: {
          docente_id: '',
          materia_id: '',
          carrera_id: '',
          cohorte_id: '',
          rol: item.rol,
          comisiones: item.comisiones,
          responsable_id: null,
          vig_desde: item.vig_desde,
          vig_hasta: item.vig_hasta,
          activo: !item.activo,
        },
      });
    } catch {
      // Error handled by query client
    }
  };

  return (
    <div>
      <PageHeader
        title="Asignaciones"
        breadcrumbs={[{ label: 'Equipos' }, { label: 'Asignaciones' }]}
        actions={
          !showForm && !editingItem
            ? [{ label: 'Nueva Asignación', onClick: () => setShowForm(true) }]
            : undefined
        }
      />

      <div className="mb-4 flex space-x-2">
        <Link
          to="/admin/equipos/asignacion-masiva"
          className="px-3 py-1.5 text-xs font-medium text-blue-600 border border-blue-300 rounded-md hover:bg-blue-50 transition-colors"
        >
          Asignación Masiva
        </Link>
        <Link
          to="/admin/equipos/clonar"
          className="px-3 py-1.5 text-xs font-medium text-blue-600 border border-blue-300 rounded-md hover:bg-blue-50 transition-colors"
        >
          Clonar Equipo
        </Link>
        <Link
          to="/admin/equipos/vigencia"
          className="px-3 py-1.5 text-xs font-medium text-blue-600 border border-blue-300 rounded-md hover:bg-blue-50 transition-colors"
        >
          Actualizar Vigencia
        </Link>
        <Link
          to="/admin/equipos/exportar"
          className="px-3 py-1.5 text-xs font-medium text-blue-600 border border-blue-300 rounded-md hover:bg-blue-50 transition-colors"
        >
          Exportar
        </Link>
      </div>

      {showForm && (
        <div className="mb-6 p-4 bg-white rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Nueva Asignación</h3>
          <AsignacionForm
            onSubmit={handleCreate}
            onCancel={() => setShowForm(false)}
            isSubmitting={createMutation.isPending}
            docentes={docentes}
            carreras={carreras}
            cohortes={cohortes}
            materias={materias}
          />
        </div>
      )}

      {isLoading ? (
        <Loading />
      ) : error ? (
        <ErrorDisplay onRetry={refetch} />
      ) : !asignaciones || asignaciones.length === 0 ? (
        <EmptyState
          title="No hay asignaciones"
          description="No se encontraron asignaciones con los filtros actuales."
          actionLabel="Nueva Asignación"
          onAction={() => setShowForm(true)}
        />
      ) : (
        <AsignacionTable
          data={asignaciones}
          filters={filters}
          onFilterChange={setFilters}
          onEdit={(item) => setEditingItem(item)}
          onToggle={handleToggle}
        />
      )}
    </div>
  );
}

export default AsignacionesPage;
