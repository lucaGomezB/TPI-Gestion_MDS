import { useState, type ReactNode } from 'react';
import { useParams } from 'react-router-dom';
import PageHeader from '@/shared/components/PageHeader';
import { useAuth } from '@/features/auth/context/AuthContext';
import { useMateria } from '../services/useMaterias';
import { useExportAtrasados } from '../services/useReportes';
import CsvExportButton from '../components/CsvExportButton';
import PermissionDenied from '../components/PermissionDenied';

function ExportAtrasadosPage(): ReactNode {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const { data: materia } = useMateria(id!);
  const exportAtrasados = useExportAtrasados();
  const [exportStatus, setExportStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!user || (user.rol !== 'PROFESOR' && user.rol !== 'ADMIN' && user.rol !== 'COORDINADOR')) {
    return <PermissionDenied requiredPermission="reportes:exportar_atrasados" />;
  }

  const handleExport = async () => {
    setExportStatus('idle');
    setErrorMessage(null);
    try {
      await exportAtrasados(id!);
      setExportStatus('success');
      setTimeout(() => setExportStatus('idle'), 3000);
    } catch {
      setExportStatus('error');
      setErrorMessage('Error al descargar el archivo. Intente nuevamente.');
    }
  };

  return (
    <div>
      <PageHeader
        title="Exportar TPs sin corregir"
        breadcrumbs={[
          { label: 'Materias', href: '/materias' },
          { label: materia?.nombre || '...', href: `/materias/${id}` },
          { label: 'Exportar atrasados' },
        ]}
      />

      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              Trabajos Practicos sin corregir
            </h3>
            <p className="text-sm text-gray-500">
              Descarga un archivo CSV con los TPs pendientes de correccion de {materia?.nombre || 'la materia'}.
              El archivo incluira nombre del alumno, actividad, fecha de entrega y comision.
            </p>
          </div>
          <CsvExportButton onExport={handleExport} label="Descargar CSV" />
        </div>

        {exportStatus === 'success' && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md text-sm text-green-700 flex items-center space-x-2">
            <svg className="w-5 h-5 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Archivo descargado correctamente.</span>
          </div>
        )}

        {exportStatus === 'error' && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700 flex items-start space-x-2">
            <svg className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
            <span>{errorMessage}</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default ExportAtrasadosPage;
