import { useState, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import AsignacionMasivaForm from '../components/AsignacionMasivaForm';
import { useDocentes } from '../hooks/useEquipos';
import { useCarreras } from '../../estructura-academica/hooks/useCarreras';
import { useCohortes } from '../../estructura-academica/hooks/useCohortes';
import { useMaterias } from '../../estructura-academica/hooks/useMaterias';
import * as asignacionesService from '../services/asignacionesService';

function AsignacionMasivaPage(): ReactNode {
  const [result, setResult] = useState<{ count: number } | null>(null);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data: docentes = [], isLoading: loadingDocentes } = useDocentes();
  const { data: carreras = [], isLoading: loadingCarreras } = useCarreras();
  const { data: cohortes = [] } = useCohortes();
  const { data: materias = [], isLoading: loadingMaterias } = useMaterias();

  const handleSubmit = async (data: Parameters<typeof asignacionesService.createAsignacionMasiva>[0]) => {
    setError('');
    setResult(null);
    setIsSubmitting(true);
    try {
      const res = await asignacionesService.createAsignacionMasiva(data);
      setResult(res);
    } catch {
      setError('Error al realizar la asignación masiva. Verifique los datos e intente nuevamente.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loadingDocentes || loadingCarreras || loadingMaterias) return <Loading />;

  return (
    <div>
      <PageHeader
        title="Asignación Masiva"
        breadcrumbs={[
          { label: 'Equipos', href: '/admin/equipos/asignaciones' },
          { label: 'Asignación Masiva' },
        ]}
      />

      {result ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
          <p className="text-sm font-medium text-green-800">
            {result.count} docentes asignados correctamente.
          </p>
          <Link
            to="/admin/equipos/asignaciones"
            className="mt-2 inline-block text-sm text-green-700 underline hover:text-green-800"
          >
            Ver asignaciones
          </Link>
        </div>
      ) : (
        <AsignacionMasivaForm
          onSubmit={handleSubmit}
          isSubmitting={isSubmitting}
          docentes={docentes}
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
    </div>
  );
}

export default AsignacionMasivaPage;
