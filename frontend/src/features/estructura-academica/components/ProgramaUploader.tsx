import { useState, useRef, type ReactNode } from 'react';
import { useUploadPrograma, useProgramas } from '../hooks/useMaterias';
import type { Carrera, Cohorte } from '../types/estructura';

interface ProgramaUploaderProps {
  materiaId: string;
  materiaNombre: string;
  carreras: Carrera[];
  cohortes: Cohorte[];
}

function ProgramaUploader({ materiaId, materiaNombre, carreras, cohortes }: ProgramaUploaderProps): ReactNode {
  const [showUpload, setShowUpload] = useState(false);
  const [titulo, setTitulo] = useState('');
  const [carreraId, setCarreraId] = useState('');
  const [cohorteId, setCohorteId] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: programas, isLoading: loadingProgramas, refetch } = useProgramas(materiaId);
  const uploadMutation = useUploadPrograma();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    setFileError('');

    if (!selected) {
      setFile(null);
      return;
    }

    if (selected.type !== 'application/pdf') {
      setFileError('Solo se aceptan archivos PDF');
      setFile(null);
      return;
    }

    if (selected.size > 10 * 1024 * 1024) {
      setFileError('El archivo no debe superar los 10MB');
      setFile(null);
      return;
    }

    setFile(selected);
  };

  const handleUpload = async () => {
    if (!file || !titulo || !carreraId || !cohorteId) return;

    try {
      await uploadMutation.mutateAsync({
        materiaId,
        carreraId,
        cohorteId,
        titulo,
        file,
      });
      setShowUpload(false);
      setTitulo('');
      setCarreraId('');
      setCohorteId('');
      setFile(null);
      refetch();
    } catch {
      // Error handled by mutation
    }
  };

  const handleDownload = (programaId: string, _filename: string) => {
    window.open(`/api/admin/programas-materia/${programaId}/download`, '_blank');
  };

  // Filter cohortes by selected carrera
  const filteredCohortes = cohortes.filter((c) => c.carrera_id === carreraId);

  return (
    <div className="mt-4 border border-gray-200 rounded-lg p-4 bg-gray-50">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-gray-700">Programa de la Materia</h4>
        {!showUpload && (
          <button
            onClick={() => setShowUpload(true)}
            className="px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
          >
            Subir Programa
          </button>
        )}
      </div>

      {showUpload && (
        <div className="space-y-3 mb-4 p-3 bg-white rounded border border-gray-200">
          <h5 className="text-sm font-medium text-gray-700">
            Nuevo Programa para: {materiaNombre}
          </h5>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Título</label>
            <input
              type="text"
              value={titulo}
              onChange={(e) => setTitulo(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Ej: Programa 2026"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Carrera</label>
              <select
                value={carreraId}
                onChange={(e) => {
                  setCarreraId(e.target.value);
                  setCohorteId('');
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Seleccione</option>
                {carreras.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nombre}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Cohorte</label>
              <select
                value={cohorteId}
                onChange={(e) => setCohorteId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={!carreraId}
              >
                <option value="">Seleccione</option>
                {filteredCohortes.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nombre}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Archivo PDF</label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              className="w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            {fileError && <p className="mt-1 text-xs text-red-600">{fileError}</p>}
            {file && <p className="mt-1 text-xs text-gray-500">{file.name} ({(file.size / 1024 / 1024).toFixed(1)} MB)</p>}
          </div>

          <div className="flex items-center justify-end space-x-2">
            <button
              onClick={() => {
                setShowUpload(false);
                setFile(null);
                setFileError('');
              }}
              className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={handleUpload}
              disabled={!file || !titulo || !carreraId || !cohorteId || uploadMutation.isPending}
              className="px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {uploadMutation.isPending ? 'Subiendo...' : 'Subir'}
            </button>
          </div>
        </div>
      )}

      {/* Programas list */}
      {loadingProgramas ? (
        <p className="text-sm text-gray-500">Cargando programas...</p>
      ) : programas && programas.length > 0 ? (
        <div className="space-y-2">
          {programas.map((prog) => (
            <div
              key={prog.id}
              className="flex items-center justify-between p-2 bg-white rounded border border-gray-200"
            >
              <div>
                <p className="text-sm font-medium text-gray-700">{prog.titulo}</p>
                <p className="text-xs text-gray-500">{prog.filename}</p>
              </div>
              <button
                onClick={() => prog.id && handleDownload(prog.id, prog.filename)}
                className="px-3 py-1 text-xs font-medium text-blue-600 border border-blue-300 rounded-md hover:bg-blue-50 transition-colors"
              >
                Descargar
              </button>
            </div>
          ))}
        </div>
      ) : (
        !showUpload && (
          <p className="text-sm text-gray-500 italic">
            No hay programas cargados para esta materia.
          </p>
        )
      )}
    </div>
  );
}

export default ProgramaUploader;
