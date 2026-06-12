import { type ReactNode } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';
import { useAuth } from '@/features/auth/context/AuthContext';
import { useMateria } from '../services/useMaterias';
import { useAtrasados } from '../services/useAtrasados';
import AtrasadosTable from '../components/AtrasadosTable';
import FilterBar from '../components/FilterBar';
import PermissionDenied from '../components/PermissionDenied';
import type { FilterField } from '../components/FilterBar';

function AtrasadosPage(): ReactNode {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const { data: materia } = useMateria(id!);

  const filters = {
    comision: searchParams.get('comision') || undefined,
    busqueda: searchParams.get('busqueda') || undefined,
    fecha_desde: searchParams.get('fecha_desde') || undefined,
    fecha_hasta: searchParams.get('fecha_hasta') || undefined,
  };

  const { data: atrasados, isLoading, error } = useAtrasados(id!, filters);
  const hasFilters = Object.values(filters).some(Boolean);

  if (!user || (user.rol !== 'PROFESOR' && user.rol !== 'ADMIN' && user.rol !== 'COORDINADOR')) {
    return <PermissionDenied requiredPermission="atrasados:ver" />;
  }

  const filterFields: FilterField[] = [
    {
      key: 'comision',
      label: 'Comision',
      type: 'select',
      options: (materia?.comisiones || []).map((c) => ({ value: c, label: c })),
    },
    { key: 'busqueda', label: 'Busqueda', type: 'text', placeholder: 'Nombre, apellido o email' },
    { key: 'fecha_desde', label: 'Fecha desde', type: 'date' },
    { key: 'fecha_hasta', label: 'Fecha hasta', type: 'date' },
  ];

  return (
    <div>
      <PageHeader
        title="Atrasados"
        breadcrumbs={[
          { label: 'Materias', href: '/materias' },
          { label: materia?.nombre || '...', href: `/materias/${id}` },
          { label: 'Atrasados' },
        ]}
      />

      <FilterBar fields={filterFields} debounceMs={300} />

      {isLoading ? (
        <>
          <Loading skeleton />
          <Loading skeleton />
        </>
      ) : error ? (
        <ErrorDisplay message="Error al cargar atrasados" />
      ) : !atrasados || atrasados.length === 0 ? (
        hasFilters ? (
          <EmptyState
            title="No se encontraron alumnos con esos filtros"
            description="Intenta ajustar los filtros para obtener resultados."
          />
        ) : (
          <EmptyState
            title="Todos los alumnos estan al dia"
            description="No se detectaron alumnos atrasados en esta materia. Todos cumplen con el minimo de actividades."
          />
        )
      ) : (
        <div>
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mb-4">
            <p className="text-sm text-blue-800">
              <span className="font-medium">{atrasados.length} {atrasados.length === 1 ? 'alumno atrasado' : 'alumnos atrasados'}</span>
              {' '}detectados en esta materia.
            </p>
          </div>
          <AtrasadosTable items={atrasados} />
        </div>
      )}
    </div>
  );
}

export default AtrasadosPage;
