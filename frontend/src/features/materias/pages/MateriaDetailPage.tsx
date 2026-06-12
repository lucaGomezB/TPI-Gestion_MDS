import { useState, type ReactNode } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';
import { useAuth } from '@/features/auth/context/AuthContext';
import { useMateria } from '../services/useMaterias';
import {
  useCalificaciones,
  useUmbral,
  useUpdateUmbral,
  useImportarCalificaciones,
  useConfirmImport,
  useVaciarCalificaciones,
} from '../services/useCalificaciones';
import { useUploadPadron, useReplacePadron } from '../services/usePadron';
import { useUploadCompletionReport, useExportCompletionReport } from '../services/useCompletionReport';
import GradeTable from '../components/GradeTable';
import ThresholdForm from '../components/ThresholdForm';
import ImportModal from '../components/ImportModal';
import PadronImportModal from '../components/PadronImportModal';
import CompletionReportImport from '../components/CompletionReportImport';
import PermissionDenied from '../components/PermissionDenied';
import type { ImportActivity, PadronImportResult, CompletionReportResult } from '../types';

function MateriaDetailPage(): ReactNode {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [importOpen, setImportOpen] = useState(false);
  const [padronOpen, setPadronOpen] = useState(false);
  const [confirmingVaciar, setConfirmingVaciar] = useState(false);
  const [vaciarError, setVaciarError] = useState<string | null>(null);
  const [vaciarSuccess, setVaciarSuccess] = useState(false);

  const { data: materia, isLoading: loadingMateria, error: errorMateria } = useMateria(id!);
  const { data: calificaciones, isLoading: loadingCalif, error: errorCalif } = useCalificaciones(id!);
  const { data: umbral, isLoading: loadingUmbral } = useUmbral(id!);
  const updateUmbral = useUpdateUmbral(id!);
  const importCalificaciones = useImportarCalificaciones(id!);
  const confirmImport = useConfirmImport(id!);
  const vaciarCalificaciones = useVaciarCalificaciones(id!);
  const uploadPadron = useUploadPadron(id!);
  const replacePadron = useReplacePadron(id!);
  const uploadCompletionReport = useUploadCompletionReport(id!);
  const exportCompletionReport = useExportCompletionReport();

  if (!user || (user.rol !== 'PROFESOR' && user.rol !== 'ADMIN' && user.rol !== 'COORDINADOR')) {
    return <PermissionDenied requiredPermission="calificaciones:ver" />;
  }

  if (loadingMateria || (loadingCalif && !calificaciones)) {
    return (
      <div>
        <PageHeader title="Cargando..." breadcrumbs={[{ label: 'Materias', href: '/materias' }, { label: 'Detalle' }]} />
        <Loading skeleton />
      </div>
    );
  }

  if (errorMateria || !materia) {
    return (
      <div>
        <PageHeader title="Error" breadcrumbs={[{ label: 'Materias', href: '/materias' }, { label: 'Detalle' }]} />
        <ErrorDisplay message="Error al cargar la materia" onRetry={() => navigate(0)} />
      </div>
    );
  }

  const handleImportUpload = async (file: File): Promise<ImportActivity[]> => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await importCalificaciones.mutateAsync(file);
    return data.actividades || [];
  };

  const handleImportConfirm = async (actividades: string[]) => {
    await confirmImport.mutateAsync(actividades);
  };

  const handlePadronUpload = async (file: File): Promise<PadronImportResult> => {
    return await uploadPadron.mutateAsync(file);
  };

  const handlePadronReplace = async (file: File): Promise<PadronImportResult> => {
    return await replacePadron.mutateAsync(file);
  };

  const handleCompletionUpload = async (file: File): Promise<CompletionReportResult> => {
    return await uploadCompletionReport.mutateAsync(file);
  };

  const handleVaciar = async () => {
    try {
      await vaciarCalificaciones.mutateAsync();
      setConfirmingVaciar(false);
      setVaciarSuccess(true);
      setVaciarError(null);
      setTimeout(() => setVaciarSuccess(false), 3000);
    } catch {
      setVaciarError('Error al vaciar los datos. Intente nuevamente.');
    }
  };

  const handleUpdateUmbral = async (value: number) => {
    await updateUmbral.mutateAsync(value);
  };

  const canEdit = user.rol === 'ADMIN' || user.rol === 'COORDINADOR';

  return (
    <div>
      <PageHeader
        title={materia.nombre}
        breadcrumbs={[
          { label: 'Materias', href: '/materias' },
          { label: materia.nombre },
        ]}
        actions={[
          { label: 'Atrasados', onClick: () => navigate(`/materias/${id}/atrasados`), variant: 'secondary' },
          { label: 'Ranking', onClick: () => navigate(`/materias/${id}/ranking`), variant: 'secondary' },
          { label: 'Reportes', onClick: () => navigate(`/materias/${id}/reportes`), variant: 'secondary' },
          { label: 'Notas Finales', onClick: () => navigate(`/materias/${id}/notas-finales`), variant: 'secondary' },
          { label: 'Seguimiento', onClick: () => navigate(`/materias/${id}/seguimiento`), variant: 'secondary' },
        ]}
      />

      <div className="mb-4">
        <p className="text-sm text-gray-500">
          Cohorte: {materia.cohorte} | Comisiones: {materia.comisiones?.join(', ') || 'Sin comisiones'}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        {loadingUmbral ? <Loading skeleton /> : (
          <ThresholdForm
            currentValue={umbral?.umbral_pct ?? 60}
            onSubmit={handleUpdateUmbral}
            disabled={updateUmbral.isPending}
          />
        )}

        {canEdit && (
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <p className="text-sm font-medium text-gray-500 mb-3">Gestion de datos</p>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setPadronOpen(true)}
                className="px-3 py-1.5 text-sm font-medium text-blue-700 border border-blue-300 rounded-md hover:bg-blue-50 transition-colors"
              >
                Importar padron
              </button>
              <button
                onClick={() => navigate(`/materias/${id}/export-atrasados`)}
                className="px-3 py-1.5 text-sm font-medium text-green-700 border border-green-300 rounded-md hover:bg-green-50 transition-colors"
              >
                Exportar atrasados
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg border border-gray-200 mb-6">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Calificaciones</h2>
          <div className="flex space-x-2">
            <button
              onClick={() => setImportOpen(true)}
              className="px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
            >
              Importar
            </button>
            {calificaciones && calificaciones.length > 0 && (
              <>
                {confirmingVaciar ? (
                  <div className="flex space-x-2 items-center">
                    <span className="text-xs text-gray-500">Se eliminaran todas las calificaciones y datos de esta materia.</span>
                    <button
                      onClick={handleVaciar}
                      disabled={vaciarCalificaciones.isPending}
                      className="px-3 py-1.5 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 transition-colors"
                    >
                      {vaciarCalificaciones.isPending ? 'Vaciando...' : 'Confirmar eliminacion'}
                    </button>
                    <button
                      onClick={() => { setConfirmingVaciar(false); setVaciarError(null); }}
                      className="px-3 py-1.5 text-sm font-medium text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                    >
                      Cancelar
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => { setConfirmingVaciar(true); setVaciarError(null); }}
                    className="px-3 py-1.5 text-sm font-medium text-red-600 border border-red-300 rounded-md hover:bg-red-50 transition-colors"
                  >
                    Vaciar datos
                  </button>
                )}
              </>
            )}
          </div>
        </div>

        {vaciarSuccess && (
          <div className="mx-4 mt-3 p-3 bg-green-50 border border-green-200 rounded-md text-sm text-green-700 flex items-center space-x-2">
            <svg className="w-5 h-5 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Datos eliminados correctamente.</span>
          </div>
        )}

        {vaciarError && (
          <div className="mx-4 mt-3 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
            {vaciarError}
          </div>
        )}

        {errorCalif ? (
          <div className="p-4">
            <ErrorDisplay message="Error al cargar calificaciones" />
          </div>
        ) : !calificaciones || calificaciones.length === 0 ? (
          <EmptyState
            title="Aun no hay calificaciones importadas"
            description="Importa un archivo .xlsx o .csv para comenzar."
            actionLabel="Importar calificaciones"
            onAction={() => setImportOpen(true)}
          />
        ) : (
          <GradeTable items={calificaciones} />
        )}
      </div>

      {canEdit && (
        <div className="mb-6">
          <CompletionReportImport
            materiaId={id!}
            onUpload={handleCompletionUpload}
            onExport={exportCompletionReport}
          />
        </div>
      )}

      <ImportModal
        isOpen={importOpen}
        onClose={() => setImportOpen(false)}
        onUpload={handleImportUpload}
        onConfirm={handleImportConfirm}
      />

      <PadronImportModal
        isOpen={padronOpen}
        onClose={() => setPadronOpen(false)}
        onUpload={handlePadronUpload}
        onReplace={handlePadronReplace}
      />
    </div>
  );
}

export default MateriaDetailPage;
