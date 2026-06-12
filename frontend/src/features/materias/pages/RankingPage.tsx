import { useState, type ReactNode } from 'react';
import { useParams } from 'react-router-dom';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';
import { useAuth } from '@/features/auth/context/AuthContext';
import { useMateria } from '../services/useMaterias';
import { useRanking } from '../services/useAtrasados';
import RankingTable from '../components/RankingTable';
import PermissionDenied from '../components/PermissionDenied';

function RankingPage(): ReactNode {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [showOnlyApproved, setShowOnlyApproved] = useState(false);
  const { data: materia } = useMateria(id!);
  const { data: ranking, isLoading, error } = useRanking(id!);

  if (!user || (user.rol !== 'PROFESOR' && user.rol !== 'ADMIN' && user.rol !== 'COORDINADOR')) {
    return <PermissionDenied requiredPermission="atrasados:ver" />;
  }

  return (
    <div>
      <PageHeader
        title="Ranking de aprobadas"
        breadcrumbs={[
          { label: 'Materias', href: '/materias' },
          { label: materia?.nombre || '...', href: `/materias/${id}` },
          { label: 'Ranking' },
        ]}
      />

      {isLoading ? (
        <Loading skeleton />
      ) : error ? (
        <ErrorDisplay message="Error al cargar el ranking" />
      ) : !ranking || ranking.length === 0 ? (
        <EmptyState
          title="No hay alumnos con actividades aprobadas"
          description="Aun no se registraron actividades aprobadas para mostrar en el ranking."
        />
      ) : (
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">
                Total: <strong className="text-gray-900">{ranking.length} alumnos</strong>
              </span>
              <label className="flex items-center space-x-2 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={showOnlyApproved}
                  onChange={(e) => setShowOnlyApproved(e.target.checked)}
                  className="rounded border-gray-300"
                />
                <span className="text-gray-600">Solo mostrar con al menos 1 actividad aprobada</span>
              </label>
            </div>
          </div>
          <RankingTable items={ranking} showOnlyApproved={showOnlyApproved} />
        </div>
      )}
    </div>
  );
}

export default RankingPage;
