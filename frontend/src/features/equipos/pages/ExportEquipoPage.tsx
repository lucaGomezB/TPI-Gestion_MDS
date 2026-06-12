import { type ReactNode } from 'react';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ExportButton from '../components/ExportButton';
import { useCarreras } from '../../estructura-academica/hooks/useCarreras';
import { useCohortes } from '../../estructura-academica/hooks/useCohortes';
import { useMaterias } from '../../estructura-academica/hooks/useMaterias';

function ExportEquipoPage(): ReactNode {
  const { data: carreras = [], isLoading: loadingCarreras } = useCarreras();
  const { data: cohortes = [] } = useCohortes();
  const { data: materias = [], isLoading: loadingMaterias } = useMaterias();

  if (loadingCarreras || loadingMaterias) return <Loading />;

  return (
    <div>
      <PageHeader
        title="Exportar Equipo"
        breadcrumbs={[
          { label: 'Equipos', href: '/admin/equipos/asignaciones' },
          { label: 'Exportar' },
        ]}
      />

      <div className="max-w-lg">
        <p className="text-sm text-gray-600 mb-4">
          Seleccione los filtros para exportar el equipo docente como archivo CSV.
        </p>
        <ExportButton
          carreras={carreras}
          cohortes={cohortes}
          materias={materias}
        />
      </div>
    </div>
  );
}

export default ExportEquipoPage;
