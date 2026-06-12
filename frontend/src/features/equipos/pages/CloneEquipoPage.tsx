import { useState, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import CloneEquipoForm from '../components/CloneEquipoForm';
import { useCarreras } from '../../estructura-academica/hooks/useCarreras';
import { useCohortes } from '../../estructura-academica/hooks/useCohortes';
import { useMaterias } from '../../estructura-academica/hooks/useMaterias';
import { useCloneEquipo } from '../hooks/useCloneEquipo';

function CloneEquipoPage(): ReactNode {
  const [result, setResult] = useState<{ count: number } | null>(null);

  const { data: carreras = [], isLoading: loadingCarreras } = useCarreras();
  const { data: cohortes = [] } = useCohortes();
  const { data: materias = [], isLoading: loadingMaterias } = useMaterias();
  const cloneMutation = useCloneEquipo();

  const handleSubmit = async (data: Parameters<typeof cloneMutation.mutateAsync>[0]) => {
    try {
      const res = await cloneMutation.mutateAsync(data);
      setResult(res);
    } catch {
      // Error handled by mutation
    }
  };

  if (loadingCarreras || loadingMaterias) return <Loading />;

  return (
    <div>
      <PageHeader
        title="Clonar Equipo"
        breadcrumbs={[
          { label: 'Equipos', href: '/admin/equipos/asignaciones' },
          { label: 'Clonar' },
        ]}
      />

      {result ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-sm font-medium text-green-800">
            {result.count} asignaciones clonadas correctamente.
          </p>
          <Link
            to="/admin/equipos/asignaciones"
            className="mt-2 inline-block text-sm text-green-700 underline hover:text-green-800"
          >
            Ver asignaciones
          </Link>
        </div>
      ) : (
        <CloneEquipoForm
          onSubmit={handleSubmit}
          isSubmitting={cloneMutation.isPending}
          carreras={carreras}
          cohortes={cohortes}
          materias={materias}
        />
      )}
    </div>
  );
}

export default CloneEquipoPage;
