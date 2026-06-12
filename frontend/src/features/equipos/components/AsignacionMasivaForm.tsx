import { useState } from 'react';
import type { Docente } from '../types/docentes';
import type { Carrera, Cohorte, Materia } from '../../estructura-academica/types/estructura';

const ROLES = ['PROFESOR', 'TUTOR', 'NEXO', 'COORDINADOR'];

interface AsignacionMasivaFormProps {
  onSubmit: (data: {
    docente_ids: string[];
    materia_id: string;
    carrera_id: string;
    cohorte_id: string;
    rol: string;
    comisiones: string[];
    responsable_id: string | null;
    vig_desde: string;
    vig_hasta: string;
  }) => void;
  isSubmitting?: boolean;
  docentes: Docente[];
  carreras: Carrera[];
  cohortes: Cohorte[];
  materias: Materia[];
}

function AsignacionMasivaForm({
  onSubmit,
  isSubmitting,
  docentes,
  carreras,
  cohortes,
  materias,
}: AsignacionMasivaFormProps) {
  const [selectedDocentes, setSelectedDocentes] = useState<string[]>([]);
  const [materiaId, setMateriaId] = useState('');
  const [carreraId, setCarreraId] = useState('');
  const [cohorteId, setCohorteId] = useState('');
  const [rol, setRol] = useState('');
  const [comisiones, setComisiones] = useState<string[]>([]);
  const [responsableId, setResponsableId] = useState<string>('');
  const [vigDesde, setVigDesde] = useState('');
  const [vigHasta, setVigHasta] = useState('');
  const [error, setError] = useState('');

  const filteredCohortes = cohortes.filter((c) => c.carrera_id === carreraId);

  const handleToggleDocente = (id: string) => {
    setSelectedDocentes((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id],
    );
  };

  const handleSelectAll = () => {
    if (selectedDocentes.length === docentes.length) {
      setSelectedDocentes([]);
    } else {
      setSelectedDocentes(docentes.map((d) => d.id ?? ''));
    }
  };

  const handleSubmit = () => {
    setError('');

    if (selectedDocentes.length === 0) {
      setError('Seleccione al menos un docente');
      return;
    }
    if (!materiaId || !carreraId || !cohorteId || !rol || !vigDesde || !vigHasta) {
      setError('Complete todos los campos requeridos');
      return;
    }

    onSubmit({
      docente_ids: selectedDocentes,
      materia_id: materiaId,
      carrera_id: carreraId,
      cohorte_id: cohorteId,
      rol,
      comisiones,
      responsable_id: responsableId || null,
      vig_desde: vigDesde,
      vig_hasta: vigHasta,
    });
  };

  return (
    <div className="space-y-6">
      {/* Academic Context */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Contexto Académico</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Rol</label>
            <select
              value={rol}
              onChange={(e) => setRol(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Seleccione</option>
              {ROLES.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Comisiones */}
        <div className="mt-3">
          <label className="block text-xs font-medium text-gray-600 mb-1">Comisiones</label>
          <div className="flex flex-wrap gap-2">
            {['A', 'B', 'C', 'D', 'E', 'F'].map((com) => (
              <label key={com} className="flex items-center space-x-1 text-sm">
                <input
                  type="checkbox"
                  checked={comisiones.includes(com)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setComisiones([...comisiones, com]);
                    } else {
                      setComisiones(comisiones.filter((c) => c !== com));
                    }
                  }}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span>Com. {com}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Vigencia */}
        <div className="grid grid-cols-2 gap-4 mt-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Vigencia Desde</label>
            <input
              type="date"
              value={vigDesde}
              onChange={(e) => setVigDesde(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Vigencia Hasta</label>
            <input
              type="date"
              value={vigHasta}
              onChange={(e) => setVigHasta(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Responsable */}
        <div className="mt-3">
          <label className="block text-xs font-medium text-gray-600 mb-1">Responsable (opcional)</label>
          <select
            value={responsableId}
            onChange={(e) => setResponsableId(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Sin responsable</option>
            {docentes.map((d) => (
              <option key={d.id} value={d.id}>{d.nombre} {d.apellidos}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Docente Selection */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-700">
            Docentes Seleccionados: {selectedDocentes.length}
          </h3>
          <button
            onClick={handleSelectAll}
            className="text-xs text-blue-600 hover:text-blue-800 font-medium"
          >
            {selectedDocentes.length === docentes.length ? 'Deseleccionar todos' : 'Seleccionar todos'}
          </button>
        </div>
        <div className="max-h-64 overflow-y-auto space-y-1">
          {docentes.map((doc) => (
            <label
              key={doc.id}
              className={`flex items-center space-x-2 p-2 rounded text-sm cursor-pointer transition-colors ${
                selectedDocentes.includes(doc.id ?? '')
                  ? 'bg-blue-50 border border-blue-200'
                  : 'hover:bg-gray-50 border border-transparent'
              }`}
            >
              <input
                type="checkbox"
                checked={selectedDocentes.includes(doc.id ?? '')}
                onChange={() => doc.id && handleToggleDocente(doc.id)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span>{doc.nombre} {doc.apellidos}</span>
              <span className="text-gray-400 text-xs">{doc.email}</span>
              <span className="text-gray-400 text-xs ml-auto">{doc.roles.join(', ')}</span>
            </label>
          ))}
        </div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex justify-end">
        <button
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting ? 'Asignando...' : `Asignar (${selectedDocentes.length} docentes)`}
        </button>
      </div>
    </div>
  );
}

export default AsignacionMasivaForm;
