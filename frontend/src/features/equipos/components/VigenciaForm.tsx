import { useState } from 'react';
import type { Carrera, Cohorte, Materia } from '../../estructura-academica/types/estructura';

interface VigenciaFormProps {
  onSubmit: (data: {
    materia_id: string;
    carrera_id: string;
    cohorte_id: string;
    vig_desde: string;
    vig_hasta: string;
  }) => void;
  isSubmitting?: boolean;
  carreras: Carrera[];
  cohortes: Cohorte[];
  materias: Materia[];
}

function VigenciaForm({ onSubmit, isSubmitting, carreras, cohortes, materias }: VigenciaFormProps) {
  const [materiaId, setMateriaId] = useState('');
  const [carreraId, setCarreraId] = useState('');
  const [cohorteId, setCohorteId] = useState('');
  const [vigDesde, setVigDesde] = useState('');
  const [vigHasta, setVigHasta] = useState('');
  const [error, setError] = useState('');

  const filteredCohortes = cohortes.filter((c) => c.carrera_id === carreraId);

  const handleSubmit = () => {
    setError('');

    if (!materiaId || !carreraId || !cohorteId) {
      setError('Seleccione un contexto académico completo');
      return;
    }
    if (!vigDesde || !vigHasta) {
      setError('Ingrese las fechas de vigencia');
      return;
    }

    onSubmit({
      materia_id: materiaId,
      carrera_id: carreraId,
      cohorte_id: cohorteId,
      vig_desde: vigDesde,
      vig_hasta: vigHasta,
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Actualizar Vigencia</h3>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Carrera</label>
          <select
            value={carreraId}
            onChange={(e) => { setCarreraId(e.target.value); setCohorteId(''); }}
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
            value={materiaId}
            onChange={(e) => setMateriaId(e.target.value)}
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
            value={cohorteId}
            onChange={(e) => setCohorteId(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={!carreraId}
          >
            <option value="">Seleccione</option>
            {filteredCohortes.map((c) => (
              <option key={c.id} value={c.id}>{c.nombre}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Nueva Vigencia Desde</label>
          <input
            type="date"
            value={vigDesde}
            onChange={(e) => setVigDesde(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Nueva Vigencia Hasta</label>
          <input
            type="date"
            value={vigHasta}
            onChange={(e) => setVigHasta(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

      <div className="flex justify-end">
        <button
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting ? 'Actualizando...' : 'Actualizar Vigencia'}
        </button>
      </div>
    </div>
  );
}

export default VigenciaForm;
