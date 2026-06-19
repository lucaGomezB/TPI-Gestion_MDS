import { useState, useRef, type ReactNode } from 'react';
import type { PadronImportResult } from '../types';

interface PadronImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (file: File) => Promise<PadronImportResult>;
  onReplace: (file: File) => Promise<PadronImportResult>;
}

type Mode = 'upload' | 'replace';

function PadronImportModal({ isOpen, onClose, onUpload, onReplace }: PadronImportModalProps): ReactNode {
  const [step, setStep] = useState<'select' | 'uploading' | 'result'>('select');
  const [mode, setMode] = useState<Mode>('upload');
  const [result, setResult] = useState<PadronImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const reset = () => {
    setStep('select');
    setMode('upload');
    setResult(null);
    setError(null);
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const validateFile = (file: File): string | null => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !['xlsx', 'csv'].includes(ext)) {
      return 'Solo se permiten archivos .xlsx o .csv.';
    }
    if (file.size > 10 * 1024 * 1024) {
      return 'El archivo no puede superar los 10MB.';
    }
    if (file.size === 0) {
      return 'El archivo esta vacio.';
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
      const importResult = mode === 'replace'
        ? await onReplace(selectedFile)
        : await onUpload(selectedFile);
      setResult(importResult);
      setStep('result');
    } catch {
      setError('Error al procesar el padron. Verifique el formato del archivo.');
      setStep('select');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={handleClose}>
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            {step === 'result' ? 'Resultado de importacion' : 'Importar padron'}
          </h2>
          <button onClick={handleClose} className="text-gray-400 hover:text-gray-600" aria-label="Cerrar">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-4">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700 flex items-start space-x-2">
              <svg className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          {step === 'select' && (
            <div>
              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-3">
                  El archivo debe contener: DNI, nombre, apellido, email y comision de cada alumno.
                </p>
                <div className="flex space-x-3 mb-4">
                  <button
                    onClick={() => setMode('upload')}
                    className={`flex-1 py-2 px-3 text-sm font-medium rounded-md border transition-colors ${
                      mode === 'upload'
                        ? 'bg-blue-50 border-blue-300 text-blue-700'
                        : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    Agregar nuevos
                  </button>
                  <button
                    onClick={() => setMode('replace')}
                    className={`flex-1 py-2 px-3 text-sm font-medium rounded-md border transition-colors ${
                      mode === 'replace'
                        ? 'bg-orange-50 border-orange-300 text-orange-700'
                        : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    Reemplazar todo
                  </button>
                </div>
                <p className="text-xs text-gray-500 mb-4">
                  {mode === 'upload'
                    ? 'Agrega nuevos alumnos al padron existente. Los duplicados se omitiran.'
                    : 'Reemplaza completamente el padron actual con los datos del archivo.'}
                </p>
              </div>

              <div
                className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-500 transition-colors"
                onClick={() => inputRef.current?.click()}
              >
                <svg className="w-12 h-12 text-gray-400 mx-auto mb-3" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
                <p className="text-sm text-gray-600 mb-1">
                  <span className="font-medium text-blue-600">Click para seleccionar</span>
                </p>
                <p className="text-xs text-gray-500">.xlsx o .csv (max. 10MB)</p>
              </div>
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
            <div className="flex flex-col items-center py-8">
              <svg className="animate-spin h-8 w-8 text-blue-600 mb-3" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <p className="text-sm text-gray-600">Procesando padron...</p>
            </div>
          )}

          {step === 'result' && result && (
            <div>
              <div className="bg-green-50 border border-green-200 rounded-md p-4 mb-4">
                <div className="flex items-center space-x-2 mb-2">
                  <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="font-medium text-green-800">Importacion completada</span>
                </div>
                <div className="grid grid-cols-3 gap-3 text-sm mt-3">
                  <div className="bg-white rounded p-2 text-center">
                    <p className="text-lg font-bold text-gray-900">{result.total_filas}</p>
                    <p className="text-xs text-gray-500">Total filas</p>
                  </div>
                  <div className="bg-white rounded p-2 text-center">
                    <p className="text-lg font-bold text-green-600">{result.importadas}</p>
                    <p className="text-xs text-gray-500">Importadas</p>
                  </div>
                  <div className="bg-white rounded p-2 text-center">
                    <p className="text-lg font-bold text-orange-600">{result.duplicadas}</p>
                    <p className="text-xs text-gray-500">Duplicadas</p>
                  </div>
                </div>
              </div>

              {result.errores && result.errores.length > 0 && (
                <div className="mb-4">
                  <p className="text-sm font-medium text-red-700 mb-1">Errores ({result.errores.length}):</p>
                  <ul className="text-xs text-red-600 space-y-0.5 list-disc list-inside">
                    {result.errores.map((err, i) => (
                      <li key={i}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="flex justify-end">
                <button
                  onClick={handleClose}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
                >
                  Cerrar
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default PadronImportModal;
