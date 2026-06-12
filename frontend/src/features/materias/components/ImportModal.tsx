import { useState, useRef, type ReactNode } from 'react';
import type { ImportActivity } from '../types';

interface ImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (file: File) => Promise<ImportActivity[]>;
  onConfirm: (actividades: string[]) => Promise<void>;
}

function ImportModal({ isOpen, onClose, onUpload, onConfirm }: ImportModalProps): ReactNode {
  const [step, setStep] = useState<'upload' | 'preview' | 'confirming'>('upload');
  const [activities, setActivities] = useState<ImportActivity[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const reset = () => {
    setStep('upload');
    setActivities([]);
    setSelected(new Set());
    setError(null);
    setSelectedFileName(null);
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const validateFile = (file: File): string | null => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !['xlsx', 'csv'].includes(ext)) {
      return 'Solo se permiten archivos .xlsx o .csv. Seleccione un archivo con formato valido.';
    }
    if (file.size > 10 * 1024 * 1024) {
      return 'El archivo no puede superar los 10MB. Reduzca el tamano o divida los datos.';
    }
    if (file.size === 0) {
      return 'El archivo esta vacio. Verifique el contenido antes de importar.';
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
    setSelectedFileName(selectedFile.name);
    setUploading(true);
    try {
      const previewData = await onUpload(selectedFile);
      if (!previewData || previewData.length === 0) {
        setError('No se detectaron actividades en el archivo. Verifique que el formato sea correcto.');
        setUploading(false);
        return;
      }
      setActivities(previewData);
      setSelected(new Set(previewData.map((a) => a.actividad)));
      setStep('preview');
    } catch {
      setError('Error al procesar el archivo. Verifique el formato de columnas e intente nuevamente.');
    } finally {
      setUploading(false);
    }
  };

  const toggleActivity = (actividad: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(actividad)) {
        next.delete(actividad);
      } else {
        next.add(actividad);
      }
      return next;
    });
  };

  const toggleAll = () => {
    if (selected.size === activities.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(activities.map((a) => a.actividad)));
    }
  };

  const handleConfirm = async () => {
    setStep('confirming');
    setError(null);
    try {
      await onConfirm(Array.from(selected));
      reset();
      onClose();
    } catch {
      setError('Error al importar las calificaciones. Revise los datos e intente nuevamente.');
      setStep('preview');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={handleClose}>
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[80vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            {step === 'upload' ? 'Importar calificaciones' : 'Confirmar importacion'}
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

          {step === 'upload' && (
            <div>
              <div
                className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-500 transition-colors"
                onClick={() => inputRef.current?.click()}
              >
                <svg className="w-12 h-12 text-gray-400 mx-auto mb-3" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
                <p className="text-sm text-gray-600 mb-1">
                  <span className="font-medium text-blue-600">Click para seleccionar</span> o arrastra el archivo
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
              {selectedFileName && !error && (
                <p className="text-sm text-gray-500 mt-2 text-center">
                  Archivo seleccionado: <span className="font-medium">{selectedFileName}</span>
                </p>
              )}
              {uploading && (
                <div className="flex flex-col items-center justify-center mt-4 space-y-2">
                  <svg className="animate-spin h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  <span className="text-sm text-gray-600">Procesando archivo...</span>
                  <p className="text-xs text-gray-400">Leyendo {activities.length === 0 ? 'datos' : `${activities.length} actividades detectadas`}</p>
                </div>
              )}
            </div>
          )}

          {step === 'preview' && (
            <div>
              <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mb-4">
                <p className="text-sm text-blue-800">
                  <span className="font-medium">Vista previa:</span> Se detectaron{' '}
                  <strong>{activities.length} actividades</strong> con{' '}
                  <strong>{activities.reduce((s, a) => s + a.filas, 0)} filas</strong> en total.
                </p>
              </div>
              <p className="text-sm text-gray-600 mb-3">
                Selecciona las actividades que deseas importar:
              </p>
              <div className="mb-3">
                <label className="flex items-center space-x-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selected.size === activities.length && activities.length > 0}
                    onChange={toggleAll}
                    className="rounded border-gray-300"
                  />
                  <span className="font-medium">Seleccionar todas</span>
                  <span className="text-xs text-gray-400">({activities.length} actividades)</span>
                </label>
              </div>
              <div className="space-y-1 max-h-48 overflow-y-auto border border-gray-200 rounded-md p-1">
                {activities.map((activity) => (
                  <label
                    key={activity.actividad}
                    className={`flex items-center justify-between p-2 rounded cursor-pointer transition-colors ${
                      selected.has(activity.actividad) ? 'bg-blue-50 hover:bg-blue-100' : 'hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={selected.has(activity.actividad)}
                        onChange={() => toggleActivity(activity.actividad)}
                        className="rounded border-gray-300"
                      />
                      <span className="text-sm font-medium">{activity.actividad}</span>
                    </div>
                    <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                      {activity.filas} filas
                    </span>
                  </label>
                ))}
              </div>
              <div className="flex justify-end space-x-3 mt-4 pt-3 border-t border-gray-100">
                <button
                  onClick={() => reset()}
                  className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                >
                  Volver
                </button>
                <button
                  onClick={handleConfirm}
                  disabled={selected.size === 0}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Importar {selected.size} {selected.size === 1 ? 'actividad' : 'actividades'}
                </button>
              </div>
            </div>
          )}

          {step === 'confirming' && (
            <div className="flex flex-col items-center py-8">
              <svg className="animate-spin h-8 w-8 text-blue-600 mb-3" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <p className="text-sm font-medium text-gray-700">Importando calificaciones...</p>
              <p className="text-xs text-gray-400 mt-1">Esto puede tomar unos segundos.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ImportModal;
