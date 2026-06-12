import { useState } from 'react';
import type { Carrera, Cohorte, Materia } from '../../estructura-academica/types/estructura';

interface CloneEquipoFormProps {
  onSubmit: (data: {
    source_materia_id: string;
    source_carrera_id: string;
    source_cohorte_id: string;
    dest_materia_id: string;
    dest_carrera_id: string;
    dest_cohorte_id: string;
  }) => void;
  isSubmitting?: boolean;
  carreras: Carrera[];
  cohortes: Cohorte[];
  materias: Materia[];
}

function CloneEquipoForm({
  onSubmit,
  isSubmitting,
  carreras,
  cohortes,
  materias,
}: CloneEquipoFormProps) {
  const [source, setSource] = useState({ materia_id: '', carrera_id: '', cohorte_id: '' });
  const [dest, setDest] = useState({ materia_id: '', carrera_id: '', cohorte_id: '' });
  const [error, setError] = useState('');

  const sourceFilteredCohortes = cohortes.filter((c) => c.carrera_id === source.carrera_id);
  const destFilteredCohortes = cohortes.filter((c) => c.carrera_id === dest.carrera_id);

  const handleSubmit = () => {
    setError('');

    if (!source.materia_id || !source.carrera_id || !source.cohorte_id) {
      setError('Complete el contexto de origen');
      return;
    }
    if (!dest.materia_id || !dest.carrera_id || !dest.cohorte_id) {
      setError('Complete el contexto de destino');
      return;
    }

    if (
      source.materia_id === dest.materia_id &&
      source.carrera_id === dest.carrera_id &&
      source.cohorte_id === dest.cohorte_id
    ) {
      setError('El origen y destino deben ser diferentes');
      return;
    }

    onSubmit({
      source_materia_id: source.materia_id,
      source_carrera_id: source.carrera_id,
      source_cohorte_id: source.cohorte_id,
      dest_materia_id: dest.materia_id,
      dest_carrera_id: dest.carrera_id,
      dest_cohorte_id: dest.cohorte_id,
    });
  };

  return (
    <div className="space-y-6">
      {/* Source */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Contexto de Origen</h3>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Carrera</label>
            <select
              value={source.carrera_id}
              onChange={(e) => setSource({ ...source, carrera_id: e.target.value, cohorte_id: '' })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Seleccione</option>
              {carreras.map((c) => (
                <option key={c.id} value={c.id}>{c.nombre}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Materia</label>
            <select
              value={source.materia_id}
              onChange={(e) => setSource({ ...source, materia_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Seleccione</option>
              {materias.map((m) => (
                <option key={m.id} value={m.id}>{m.nombre}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Cohorte</label>
            <select
              value={source.cohorte_id}
              onChange={(e) => setSource({ ...source, cohorte_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={!source.carrera_id}
            >
              <option value="">Seleccione</option>
              {sourceFilteredCohortes.map((c) => (
                <option key={c.id} value={c.id}>{c.nombre}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Destination */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Contexto de Destino</h3>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Carrera</label>
            <select
              value={dest.carrera_id}
              onChange={(e) => setDest({ ...dest, carrera_id: e.target.value, cohorte_id: '' })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Seleccione</option>
              {carreras.map((c) => (
                <option key={c.id} value={c.id}>{c.nombre}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Materia</label>
            <select
              value={dest.materia_id}
              onChange={(e) => setDest({ ...dest, materia_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Seleccione</option>
              {materias.map((m) => (
                <option key={m.id} value={m.id}>{m.nombre}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Cohorte</label>
            <select
              value={dest.cohorte_id}
              onChange={(e) => setDest({ ...dest, cohorte_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={!dest.carrera_id}
            >
              <option value="">Seleccione</option>
              {destFilteredCohortes.map((c) => (
                <option key={c.id} value={c.id}>{c.nombre}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex justify-end">
        <button
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting ? 'Clonando...' : 'Clonar Equipo'}
        </button>
      </div>
    </div>
  );
}

export default CloneEquipoForm;
