import { useState, useRef, type ReactNode } from 'react';
import type { CompletionReportResult } from '../types';
import CsvExportButton from './CsvExportButton';

interface CompletionReportImportProps {
  materiaId: string;
  onUpload: (file: File) => Promise<CompletionReportResult>;
  onExport: (materiaId: string) => Promise<void>;
}

function CompletionReportImport({ materiaId, onUpload, onExport }: CompletionReportImportProps): ReactNode {
  const [step, setStep] = useState<'upload' | 'uploading' | 'result'>('upload');
  const [result, setResult] = useState<CompletionReportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const reset = () => {
    setStep('upload');
    setResult(null);
    setError(null);
  };

  const validateFile = (file: File): string | null => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !['xlsx', 'csv'].includes(ext)) {
      return 'Solo se permiten archivos .xlsx o .csv.';
    }
    if (file.size > 10 * 1024 * 1024) {
      return 'El archivo no puede superar los 10MB.';
    }
    return null;
  };

  const handleFileSelect = async (selectedFile: File) => {
    const validationError = validateFile(selectedFile);
    if (validationError) {
      setError(validationError);
      return;
    }

    setError(null);
    setStep('uploading');

    try {
      const reportResult = await onUpload(selectedFile);
      setResult(reportResult);
      setStep('result');
    } catch {
      setError('Error al procesar el reporte de completitud. Verifique el formato.');
      setStep('upload');
    }
  };

  const pendientesCount = result?.total_pendientes ?? 0;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h3 className="text-base font-semibold text-gray-900 mb-1">Reporte de completitud</h3>
      <p className="text-sm text-gray-500 mb-4">
        Importa un archivo con el estado de entrega de TPs para detectar pendientes de correccion.
      </p>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700 flex items-start space-x-2">
          <svg className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {step === 'upload' && (
        <div
          className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-blue-500 transition-colors"
          onClick={() => inputRef.current?.click()}
        >
          <svg className="w-10 h-10 text-gray-400 mx-auto mb-2" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
          <p className="text-sm text-gray-600 mb-1">
            <span className="font-medium text-blue-600">Click para seleccionar</span>
          </p>
          <p className="text-xs text-gray-500">.xlsx o .csv (max. 10MB)</p>
          <input
            ref={inputRef}
            type="file"
            accept=".xlsx,.csv"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFileSelect(f);
            }}
          />
        </div>
      )}

      {step === 'uploading' && (
        <div className="flex flex-col items-center py-6">
          <svg className="animate-spin h-8 w-8 text-blue-600 mb-3" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-sm text-gray-600">Procesando reporte...</p>
        </div>
      )}

      {step === 'result' && result && (
        <div>
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mb-4">
            <div className="grid grid-cols-3 gap-3 text-sm">
              <div className="text-center">
                <p className="text-lg font-bold text-gray-900">{result.total_alumnos}</p>
                <p className="text-xs text-gray-500">Alumnos</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-bold text-green-600">{result.total_completados}</p>
                <p className="text-xs text-gray-500">Completados</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-bold text-red-600">{result.total_pendientes}</p>
                <p className="text-xs text-gray-500">Pendientes</p>
              </div>
            </div>
          </div>

          {result.items.length > 0 && (
            <div className="mb-4">
              <p className="text-sm font-medium text-gray-700 mb-2">
                Detalle de TPs pendientes ({pendientesCount}):
              </p>
              <div className="max-h-48 overflow-y-auto border border-gray-200 rounded-md">
                <table className="min-w-full divide-y divide-gray-200 text-xs">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium text-gray-500 uppercase">Alumno</th>
                      <th className="px-3 py-2 text-left font-medium text-gray-500 uppercase">Actividad</th>
                      <th className="px-3 py-2 text-left font-medium text-gray-500 uppercase">Estado</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {result.items.map((item) => (
                      <tr key={`${item.alumno_id}-${item.actividad}`} className="hover:bg-gray-50">
                        <td className="px-3 py-2 text-gray-900">{item.apellidos}, {item.nombre}</td>
                        <td className="px-3 py-2 text-gray-500">{item.actividad}</td>
                        <td className="px-3 py-2">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                            item.estado === 'completado'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {item.estado === 'completado' ? 'Completado' : 'Pendiente'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div className="flex justify-between items-center pt-3 border-t border-gray-100">
            <button
              onClick={reset}
              className="px-3 py-1.5 text-sm font-medium text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Importar otro
            </button>
            <div className="flex space-x-2">
              <CsvExportButton
                onExport={() => onExport(materiaId)}
                label="Exportar pendientes"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default CompletionReportImport;
