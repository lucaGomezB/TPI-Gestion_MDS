import { useState } from 'react';
import { useExportEquipo } from '../hooks/useExportEquipo';
import type { Carrera, Cohorte, Materia } from '../../estructura-academica/types/estructura';

interface ExportButtonProps {
  carreras: Carrera[];
  cohortes: Cohorte[];
  materias: Materia[];
}

function ExportButton({ carreras, cohortes, materias }: ExportButtonProps) {
  const [showFilters, setShowFilters] = useState(false);
  const [materiaId, setMateriaId] = useState('');
  const [carreraId, setCarreraId] = useState('');
  const [cohorteId, setCohorteId] = useState('');
  const [error, setError] = useState('');
  const { exportData, isExporting } = useExportEquipo();

  const filteredCohortes = cohortes.filter((c) => c.carrera_id === carreraId);

  const handleExport = async () => {
    setError('');

    if (!materiaId && !carreraId && !cohorteId) {
      setError('Seleccione al menos un filtro');
      return;
    }

    await exportData(
      {
        materia_id: materiaId || undefined,
        carrera_id: carreraId || undefined,
        cohorte_id: cohorteId || undefined,
      },
      `equipo-${carreraId ? 'carrera' : 'general'}.csv`,
    );

    setShowFilters(false);
  };

  return (
    <div>
      <button
        onClick={() => setShowFilters(!showFilters)}
        className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 transition-colors"
      >
        {isExporting ? 'Exportando...' : 'Exportar CSV'}
      </button>

      {showFilters && (
        <div className="mt-3 p-4 bg-white rounded-lg shadow-sm border border-gray-200">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">
            Filtros de Exportación
          </h4>
          <div className="grid grid-cols-3 gap-4 mb-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Carrera</label>
              <select
                value={carreraId}
                onChange={(e) => { setCarreraId(e.target.value); setCohorteId(''); }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todas</option>
                {carreras.map((c) => (
                  <option key={c.id} value={c.id}>{c.nombre}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Materia</label>
              <select
                value={materiaId}
                onChange={(e) => setMateriaId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todas</option>
                {materias.map((m) => (
                  <option key={m.id} value={m.id}>{m.nombre}</option>
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
                <option value="">Todas</option>
                {filteredCohortes.map((c) => (
                  <option key={c.id} value={c.id}>{c.nombre}</option>
                ))}
              </select>
            </div>
          </div>
          {error && <p className="text-sm text-red-600 mb-2">{error}</p>}
          <div className="flex justify-end">
            <button
              onClick={handleExport}
              disabled={isExporting}
              className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {isExporting ? 'Exportando...' : 'Descargar CSV'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ExportButton;
