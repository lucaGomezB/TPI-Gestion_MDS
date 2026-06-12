import { useState, type ReactNode } from 'react';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import VigenciaForm from '../components/VigenciaForm';
import { useCarreras } from '../../estructura-academica/hooks/useCarreras';
import { useCohortes } from '../../estructura-academica/hooks/useCohortes';
import { useMaterias } from '../../estructura-academica/hooks/useMaterias';
import * as asignacionesService from '../services/asignacionesService';

function VigenciaPage(): ReactNode {
  const [result, setResult] = useState<{ count: number } | null>(null);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data: carreras = [], isLoading: loadingCarreras } = useCarreras();
  const { data: cohortes = [] } = useCohortes();
  const { data: materias = [], isLoading: loadingMaterias } = useMaterias();

  const handleSubmit = async (data: Parameters<typeof asignacionesService.updateVigenciaBulk>[0]) => {
    setError('');
    setResult(null);
    setIsSubmitting(true);
    try {
      const res = await asignacionesService.updateVigenciaBulk(data);
      setResult(res);
    } catch {
      setError('Error al actualizar la vigencia. Verifique los datos e intente nuevamente.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loadingCarreras || loadingMaterias) return <Loading />;

  return (
    <div>
      <PageHeader
        title="Actualizar Vigencia"
        breadcrumbs={[
          { label: 'Equipos', href: '/admin/equipos/asignaciones' },
          { label: 'Vigencia' },
        ]}
      />

      {result ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-sm font-medium text-green-800">
            {result.count} asignaciones actualizadas correctamente.
          </p>
        </div>
      ) : (
        <VigenciaForm
          onSubmit={handleSubmit}
          isSubmitting={isSubmitting}
          carreras={carreras}
          cohortes={cohortes}
          materias={materias}
        />
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mt-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {result && result.count === 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mt-4">
          <p className="text-sm text-yellow-700">
            No hay asignaciones en ese contexto.
          </p>
        </div>
      )}
    </div>
  );
}

export default VigenciaPage;
